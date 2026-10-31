"""The TMS client against a real local TCP server, including every documented fault."""

import asyncio
import socket
import time
import unittest

from service.adapters.tms import fake as faults
from service.adapters.tms.client import BookingDisabled, TmsClient, TmsSettings
from service.adapters.tms.fake import FakeTMS, make_load
from service.core.ports import BookingOutcome, TmsUnavailable
from service.tests.support import NetworkBlocked, client_for


class NetworkGuardTests(unittest.IsolatedAsyncioTestCase):
    def test_blocks_plain_sockets(self):
        with socket.socket() as connection, self.assertRaises(NetworkBlocked):
            connection.connect(("192.0.2.1", 80))

    async def test_blocks_the_client(self):
        client = TmsClient(TmsSettings("192.0.2.1", 80, "token"))
        with self.assertRaises((NetworkBlocked, TmsUnavailable)) as caught:
            await client._exchange(b"x")
        self.assertIsInstance(caught.exception, NetworkBlocked)


class ReadTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_maps_to_pdf_fields(self):
        async with FakeTMS([make_load("LD1", RATE="2709", MAX_BUY="2922")]) as tms:
            load = await client_for(tms).get("LD1")
        self.assertEqual((load.load_id, load.loadboard_rate, load.max_rate), ("LD1", 2709, 2922))
        self.assertEqual(load.dimensions, "636 x 96 x 108 in")
        self.assertEqual(str(load.origin), "Dallas, TX 75201")

    async def test_unknown_load_is_none_for_both_error_codes(self):
        async with FakeTMS([]) as tms:
            self.assertIsNone(await client_for(tms).get("LD404"))
        self.assertEqual(len(tms.requests), 1)

    async def test_a_missing_ceiling_is_none(self):
        load_data = make_load("LD1")
        del load_data["MAX_BUY"]
        async with FakeTMS([load_data]) as tms:
            load = await client_for(tms).get("LD1")
        self.assertIsNone(load.max_rate)

    async def test_query_sends_only_established_filters(self):
        async with FakeTMS([make_load("LD1"), make_load("LD2", EQTYPE="REEFER")]) as tms:
            loads = await client_for(tms).query(
                equipment="dry_van", origin_state="tx", dest_state="ga", origin_city="Dal", limit=5
            )
        self.assertEqual([load.load_id for load in loads], ["LD1"])
        self.assertEqual(
            tms.requests,
            ["CMD:LOAD_QUERY|AUTH:<token>|EQTYPE:DRY_VAN|ORIG_STATE:TX|DEST_STATE:GA"
             "|ORIG_CITY:Dal|MAX_RESULTS:5"],
        )

    async def test_query_rejects_bad_input_before_connecting(self):
        async with FakeTMS([]) as tms:
            client = client_for(tms)
            for kwargs in (
                {},
                {"equipment": "TANKER"},
                {"origin_state": "Texas"},
                {"equipment": "DRY_VAN", "limit": 0},
                {"equipment": "DRY_VAN", "limit": "3"},
                {"pickup_date": "2026-10-31"},
            ):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    await client.query(**kwargs)
        self.assertEqual(tms.requests, [])

    async def test_search_results_keep_their_actual_status(self):
        loads = [make_load("LD1"), make_load("LD2", STATUS="PENDING")]
        async with FakeTMS(loads) as tms:
            found = await client_for(tms).query(equipment="DRY_VAN")
        self.assertEqual({load.load_id: load.status for load in found},
                         {"LD1": "OPEN", "LD2": "PENDING"})

    async def test_a_multi_record_reply_may_exceed_one_frame(self):
        notes = "x" * 400
        loads = [make_load(f"LD{i}", NOTES=notes, ORIG_CITY="C" * 300) for i in range(20)]
        async with FakeTMS(loads) as tms:
            found = await client_for(tms).query(equipment="DRY_VAN", limit=20)
        self.assertEqual(len(found), 20)

    async def test_echo_bypasses_faults(self):
        async with FakeTMS([]) as tms:
            tms.inject(faults.SILENT)
            record = await client_for(tms).echo()
            self.assertEqual(record["MSG"], "HELLO")
            self.assertEqual(len(tms.faults), 1)

    async def test_bad_token_is_not_retried_and_stays_hidden(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            client = client_for(tms, token="wrong-token")
            with self.assertRaises(TmsUnavailable) as caught:
                await client.get("LD1")
        self.assertEqual(len(tms.requests), 1)
        self.assertNotIn("wrong-token", str(caught.exception))

    async def test_settings_hide_the_token_from_repr(self):
        self.assertNotIn("secret", repr(TmsSettings("h", 1, "secret")))


class ReadFaultTests(unittest.IsolatedAsyncioTestCase):
    async def test_recovers_from_each_fault_on_retry(self):
        for fault in (faults.SILENT, faults.LOST, faults.PARTIAL, faults.CUT_AT_LINE,
                      faults.MALFORMED, faults.TRAILING, faults.SERVER_ERROR):
            with self.subTest(fault=fault):
                async with FakeTMS([make_load("LD1")]) as tms:
                    tms.inject(fault)
                    load = await client_for(tms).get("LD1")
                self.assertEqual(load.load_id, "LD1")
                self.assertEqual(len(tms.requests), 2)

    async def test_gives_up_after_three_attempts(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            tms.inject(faults.PARTIAL, faults.MALFORMED, faults.CUT_AT_LINE)
            with self.assertRaises(TmsUnavailable):
                await client_for(tms).get("LD1")
        self.assertEqual(len(tms.requests), 3)

    async def test_respects_the_read_budget(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            tms.inject(faults.SILENT, faults.SILENT, faults.SILENT)
            client = client_for(tms, read_budget_seconds=0.3, attempt_seconds=0.2)
            started = time.monotonic()
            with self.assertRaises(TmsUnavailable):
                await client.get("LD1")
        self.assertLess(time.monotonic() - started, 0.8)

    async def test_stops_at_end_without_waiting_for_close(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            tms.inject(faults.DELAYED_CLOSE)
            started = time.monotonic()
            await client_for(tms).get("LD1")
        self.assertLess(time.monotonic() - started, 0.2)
        self.assertEqual(len(tms.requests), 1)

    async def test_reassembles_a_reply_split_across_chunks(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            tms.inject(faults.SPLIT)
            load = await client_for(tms).get("LD1")
        self.assertEqual(load.load_id, "LD1")
        self.assertEqual(len(tms.requests), 1)

    async def test_an_oversized_line_is_a_failed_read(self):
        async with FakeTMS([make_load("LD1", NOTES="x" * 5000)]) as tms:
            with self.assertRaises(TmsUnavailable):
                await client_for(tms).get("LD1")
        self.assertEqual(len(tms.requests), 3)

    async def test_a_closed_port_is_unavailable(self):
        async with FakeTMS([]) as tms:
            port = tms.port
        client = TmsClient(TmsSettings("127.0.0.1", port, "t", read_budget_seconds=0.5,
                                       attempt_seconds=0.1))
        with self.assertRaises(TmsUnavailable):
            await client.get("LD1")


class BookingTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabled_by_default_and_opens_no_connection(self):
        self.assertFalse(TmsSettings("h", 1, "t").booking_enabled)
        async with FakeTMS([make_load("LD1")]) as tms:
            client = client_for(tms, booking_enabled=False)
            with self.assertRaises(BookingDisabled):
                await client.book("LD1", "138328", 2000)
        self.assertEqual(tms.requests, [])

    async def test_sends_a_plain_integer_once(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            receipt = await client_for(tms).book("LD1", "138328", 2000)
        self.assertIs(receipt.outcome, BookingOutcome.ACK_PENDING)
        self.assertEqual(receipt.reference, "FAKE000000000001")
        self.assertEqual(
            tms.requests,
            ["CMD:LOAD_BOOK|AUTH:<token>|LOAD_ID:LD1|MC_NUM:138328|AGREED_RATE:2000"],
        )

    async def test_rejects_bad_input_before_connecting(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            client = client_for(tms)
            for mc, rate in (("138328", 0), ("138328", -1), ("138328", 1324.5),
                             ("138328", "2000"), ("MC138328", 2000), ("1|2", 2000)):
                with self.subTest(mc=mc, rate=rate), self.assertRaises(ValueError):
                    await client.book("LD1", mc, rate)
        self.assertEqual(tms.requests, [])

    async def test_a_lost_or_unclear_reply_is_unknown_and_never_retried(self):
        for fault in (faults.SILENT, faults.LOST, faults.PARTIAL, faults.CUT_AT_LINE,
                      faults.MALFORMED, faults.TRAILING, faults.SERVER_ERROR):
            with self.subTest(fault=fault):
                async with FakeTMS([make_load("LD1")]) as tms:
                    tms.inject(fault)
                    receipt = await client_for(tms).book("LD1", "138328", 2000)
                self.assertIs(receipt.outcome, BookingOutcome.UNKNOWN)
                self.assertEqual(len(tms.requests), 1)

    async def test_a_repeat_is_already_booked_and_unknown(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            client = client_for(tms)
            await client.book("LD1", "138328", 2000)
            receipt = await client.book("LD1", "138328", 2000)
        self.assertIs(receipt.outcome, BookingOutcome.UNKNOWN)
        self.assertEqual(receipt.reason, "already_booked")

    async def test_an_unknown_load_is_rejected(self):
        async with FakeTMS([]) as tms:
            receipt = await client_for(tms).book("LD404", "138328", 2000)
        self.assertIs(receipt.outcome, BookingOutcome.REJECTED)

    async def test_a_closed_port_is_unknown(self):
        async with FakeTMS([]) as tms:
            client = client_for(tms)
        receipt = await client.book("LD1", "138328", 2000)
        self.assertIs(receipt.outcome, BookingOutcome.UNKNOWN)

    async def test_the_token_never_reaches_a_stored_reply(self):
        async with FakeTMS([make_load("LD1", NOTES="")]) as tms:
            client = client_for(tms)
            original = client._exchange

            async def echoing(request):
                await original(request)
                return f"ERR|CODE:ODD|MSG:token {tms.token} seen\r\n".encode()

            client._exchange = echoing
            receipt = await client.book("LD1", "138328", 2000)
        self.assertNotIn(tms.token, receipt.raw_reply)


if __name__ == "__main__":
    unittest.main()
