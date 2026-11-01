"""Booking rules from architecture section 6.6, end to end against the local fake TMS."""

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from service.adapters.tms import fake as faults
from service.adapters.tms.fake import FakeTMS, make_load
from service.adapters.tms.mapping import to_load, to_summary
from service.core.booking import (
    BookingConflict,
    BookingService,
    InMemoryBookingStore,
    OperationConflict,
    RepDecision,
    State,
    agent_view,
)
from service.core.loads import MAX_OFFERS, select_offers
from service.core.ports import BookingOutcome, BookingReceipt, TmsUnavailable
from service.tests.support import client_for

MC = "138328"


def request(service, load_id="LD1", call_id="call-1", operation_id="op-1", rate=2000):
    return service.request(
        call_id=call_id, operation_id=operation_id, load_id=load_id, mc=MC, rate=rate,
        agreement_version="v1",
    )


class SimulatedCrash(BaseException):
    pass


class ScriptedTms:
    """For moments a real server cannot stage, such as a crash during the send."""

    booking_enabled = True

    def __init__(self, load, on_book):
        self.load = load
        self.on_book = on_book
        self.sends = 0

    async def get(self, load_id):
        return self.load

    async def book(self, load_id, mc, rate):
        self.sends += 1
        return await self.on_book()


class Base(unittest.IsolatedAsyncioTestCase):
    def service_for(self, tms, **overrides):
        self.store = InMemoryBookingStore()
        return BookingService(self.store, client_for(tms, **overrides))


class SubmitTests(Base):
    async def test_books_once_and_keeps_the_reference(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            booking = await request(self.service_for(tms))
        self.assertIs(booking.state, State.ACK_PENDING)
        self.assertEqual(booking.reference, "FAKE000000000001")
        self.assertEqual(booking.tms_status, "PENDING")
        self.assertIn("BOOKING_REF", booking.raw_reply)
        self.assertIsNotNone(booking.write_intent_id)
        self.assertFalse(booking.review_required)
        self.assertEqual(len(tms.book_requests), 1)

    async def test_rechecks_the_load_before_sending(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            await request(self.service_for(tms))
        self.assertEqual([line.split("|")[0] for line in tms.requests],
                         ["CMD:LOAD_GET", "CMD:LOAD_BOOK"])

    async def test_a_direct_booked_reply_is_confirmed(self):
        async with FakeTMS([make_load("LD1")], booking_status="BOOKED") as tms:
            booking = await request(self.service_for(tms))
        self.assertIs(booking.state, State.CONFIRMED)

    async def test_live_booking_is_off_unless_enabled(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            booking = await request(self.service_for(tms, booking_enabled=False))
        self.assertIs(booking.state, State.FAILED)
        self.assertEqual(booking.reason, "live_booking_disabled")
        self.assertEqual(tms.requests, [])

    async def test_a_bad_rate_never_creates_a_booking(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            for rate in (0, -1, 1324.5, "2000", True):
                with self.subTest(rate=rate), self.assertRaises(ValueError):
                    await request(service, rate=rate)
        self.assertEqual(self.store.bookings, {})

    async def test_nothing_is_sent_when_the_load_cannot_be_booked(self):
        without_ceiling = make_load("LD1")
        del without_ceiling["MAX_BUY"]
        cases = (
            ([], "load_gone"),
            ([make_load("LD1", STATUS="PENDING")], "load_gone"),
            ([make_load("LD1", STATUS="EXPIRED")], "load_gone"),
            ([make_load("LD1", MAX_BUY="1999")], "ceiling_fell"),
            ([without_ceiling], "ceiling_unavailable"),
        )
        for loads, reason in cases:
            with self.subTest(reason=reason, loads=loads):
                async with FakeTMS(loads) as tms:
                    booking = await request(self.service_for(tms))
                self.assertIs(booking.state, State.FAILED)
                self.assertEqual(booking.reason, reason)
                self.assertEqual(tms.book_requests, [])

    async def test_no_rate_above_the_ceiling_ever_reaches_load_book(self):
        for rate in (2299, 2300, 2301, 9999):
            with self.subTest(rate=rate):
                async with FakeTMS([make_load("LD1", MAX_BUY="2300")]) as tms:
                    await request(self.service_for(tms), rate=rate)
                sent = [int(request_["AGREED_RATE"]) for request_ in tms.book_requests]
                self.assertTrue(all(value <= 2300 for value in sent))
                self.assertEqual(len(sent), 1 if rate <= 2300 else 0)

    async def test_a_tms_outage_before_sending_fails_cleanly(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            tms.inject(faults.PARTIAL, faults.PARTIAL, faults.PARTIAL)
            booking = await request(self.service_for(tms))
        self.assertIs(booking.state, State.FAILED)
        self.assertEqual(booking.reason, "tms_unavailable")
        self.assertEqual(tms.book_requests, [])

    async def test_a_definitive_rejection_frees_the_load(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            del tms.board["LD1"]
            first = await request(service)
            self.assertIs(first.state, State.FAILED)
            self.assertEqual(await self.store.blocked_load_ids(), frozenset())
            tms.board["LD1"] = make_load("LD1")
            second = await request(service, call_id="call-2", operation_id="op-2")
        self.assertIs(second.state, State.ACK_PENDING)

    async def test_a_rejected_send_is_failed(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            original = service.tms.get

            async def vanish_after_read(load_id):
                load = await original(load_id)
                tms.board.pop("LD1")
                return load

            service.tms.get = vanish_after_read
            booking = await request(service)
        self.assertIs(booking.state, State.FAILED)
        self.assertEqual(booking.reason, "not_found")
        self.assertIn("NOT_FOUND", booking.raw_reply)


class UnknownTests(Base):
    async def test_an_unclear_send_is_unknown_and_stays_blocked(self):
        for fault in (faults.SILENT, faults.PARTIAL, faults.MALFORMED, faults.SERVER_ERROR):
            with self.subTest(fault=fault):
                async with FakeTMS([make_load("LD1")]) as tms:
                    tms.faults.extend([None, fault])
                    booking = await request(self.service_for(tms))
                self.assertIs(booking.state, State.UNKNOWN)
                self.assertTrue(booking.review_required)
                self.assertEqual(await self.store.blocked_load_ids(), {"LD1"})
                self.assertEqual(len(tms.book_requests), 1)

    async def test_already_booked_is_unknown_not_confirmed(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            tms.bookings["LD1"] = {"BOOKING_REF": "OLD"}
            booking = await request(self.service_for(tms))
        self.assertIs(booking.state, State.UNKNOWN)
        self.assertEqual(booking.reason, "already_booked")

    async def test_a_stale_open_read_never_allows_a_resend(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            tms.faults.extend([None, faults.LOST])
            service = self.service_for(tms)
            booking = await request(service)
            self.assertIs(booking.state, State.UNKNOWN)
            self.assertEqual(tms.board["LD1"]["STATUS"], "OPEN")

            reconciled = await service.reconcile(booking.id)
            self.assertIs(reconciled.state, State.UNKNOWN)
            self.assertEqual(reconciled.tms_status, "OPEN")
            with self.assertRaises(BookingConflict):
                await request(service, call_id="call-2", operation_id="op-2")
            repeated = await request(service)
        self.assertEqual(repeated.id, booking.id)
        self.assertEqual(sum("LOAD_BOOK" in line for line in tms.requests), 1)
        self.assertEqual(await self.store.blocked_load_ids(), {"LD1"})


class ConcurrencyTests(Base):
    async def test_simultaneous_calls_produce_exactly_one_send(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            results = await asyncio.gather(
                *(request(service, call_id=f"call-{i}", operation_id=f"op-{i}") for i in range(8)),
                return_exceptions=True,
            )
        self.assertEqual(sum(isinstance(result, BookingConflict) for result in results), 7)
        self.assertEqual(len(tms.book_requests), 1)

    async def test_a_repeated_operation_acts_once(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            results = await asyncio.gather(*(request(service) for _ in range(8)))
        self.assertEqual({booking.id for booking in results}, {results[0].id})
        self.assertEqual(len(tms.book_requests), 1)

    async def test_an_operation_id_cannot_change_its_inputs(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            await request(service, rate=2000)
            with self.assertRaises(OperationConflict):
                await request(service, rate=2100)

    async def test_a_call_has_at_most_one_active_booking(self):
        async with FakeTMS([make_load("LD1"), make_load("LD2")]) as tms:
            service = self.service_for(tms)
            await request(service, load_id="LD1")
            with self.assertRaises(BookingConflict):
                await request(service, load_id="LD2", operation_id="op-2")
        self.assertEqual(len(tms.book_requests), 1)


class RecoveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.load = to_load(make_load("LD1"))
        self.store = InMemoryBookingStore()

    async def test_a_crash_during_the_send_becomes_unknown_without_resending(self):
        async def crash():
            raise SimulatedCrash()

        tms = ScriptedTms(self.load, crash)
        service = BookingService(self.store, tms)
        with self.assertRaises(SimulatedCrash):
            await request(service)
        booking = next(iter(self.store.bookings.values()))
        self.assertIs(booking.state, State.SUBMITTING)
        self.assertIsNotNone(booking.write_intent_id)

        restarted = BookingService(self.store, tms)
        [recovered] = await restarted.recover()
        self.assertIs(recovered.state, State.UNKNOWN)
        self.assertTrue(recovered.review_required)
        self.assertEqual(await request(restarted), recovered)
        self.assertEqual(tms.sends, 1)

    async def test_a_crash_before_the_send_fails_and_frees_the_load(self):
        class CrashingRead(ScriptedTms):
            async def get(self, load_id):
                raise SimulatedCrash()

        service = BookingService(self.store, CrashingRead(self.load, None))
        with self.assertRaises(SimulatedCrash):
            await request(service)
        [recovered] = await service.recover()
        self.assertIs(recovered.state, State.FAILED)
        self.assertEqual(recovered.reason, "interrupted_before_send")
        self.assertEqual(await self.store.blocked_load_ids(), frozenset())

    async def test_recovery_preserves_a_known_pending_receipt(self):
        async def acknowledge():
            return BookingReceipt(BookingOutcome.ACK_PENDING, "REF1", "PENDING", "raw")

        service = BookingService(self.store, ScriptedTms(self.load, acknowledge))
        booking = await request(service)
        self.assertEqual(await service.recover(), [])
        self.assertEqual(await self.store.get(booking.id), booking)

    async def test_a_late_reply_cannot_change_a_recovered_state_but_is_kept(self):
        async def recover_then_reply():
            await service.recover()
            return BookingReceipt(BookingOutcome.ACK_PENDING, "REF1", "PENDING", "raw")

        service = BookingService(self.store, ScriptedTms(self.load, recover_then_reply))
        booking = await request(service)
        self.assertIs(booking.state, State.UNKNOWN)
        self.assertEqual(booking.reference, "REF1")
        self.assertEqual(booking.reason, "late_reply")
        self.assertTrue(booking.review_required)

    async def test_a_late_unknown_cannot_downgrade_newer_evidence(self):
        async def confirm_then_time_out():
            booking = next(iter(self.store.bookings.values()))
            await self.store.update(booking.id, frozenset({State.SUBMITTING}),
                                    state=State.CONFIRMED, reference="REF1")
            return BookingReceipt(BookingOutcome.UNKNOWN, reason="TimeoutError")

        service = BookingService(self.store, ScriptedTms(self.load, confirm_then_time_out))
        booking = await request(service)
        self.assertIs(booking.state, State.CONFIRMED)
        self.assertEqual(booking.reference, "REF1")


class RepTests(Base):
    async def test_confirming_records_a_fact_and_writes_nothing_to_the_tms(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            before = list(tms.requests)
            confirmed = await service.confirm(booking.id, "rep-1")
            self.assertEqual(tms.requests, before)
        self.assertIs(confirmed.rep_decision, RepDecision.CONFIRMED)
        self.assertIs(confirmed.state, State.ACK_PENDING)
        self.assertEqual(confirmed.tms_status, "PENDING")

    async def test_a_decline_keeps_the_load_blocked_and_flagged(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            declined = await service.decline(booking.id, "rep-1")
            self.assertIs(declined.rep_decision, RepDecision.DECLINED)
            self.assertIs(declined.state, State.ACK_PENDING)
            self.assertTrue(declined.review_required)
            self.assertEqual(declined.reason, "needs_release")
            self.assertEqual(await self.store.blocked_load_ids(), {"LD1"})
            with self.assertRaises(BookingConflict):
                await request(service, call_id="call-2", operation_id="op-2")

    async def test_a_decision_cannot_be_reversed(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            await service.confirm(booking.id, "rep-1")
            await service.confirm(booking.id, "rep-1")
            with self.assertRaises(ValueError):
                await service.decline(booking.id, "rep-2")

    async def test_a_failed_booking_has_nothing_to_confirm(self):
        async with FakeTMS([]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            with self.assertRaises(ValueError):
                await service.confirm(booking.id, "rep-1")


class ReconcileTests(Base):
    async def test_a_steady_pending_read_changes_nothing(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            reconciled = await service.reconcile(booking.id)
        self.assertEqual(reconciled, booking)

    async def test_a_bare_booked_status_does_not_confirm(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            tms.simulate_final_booking("LD1")
            reconciled = await service.reconcile(booking.id)
        self.assertIs(reconciled.state, State.ACK_PENDING)
        self.assertEqual(reconciled.tms_status, "BOOKED")
        self.assertTrue(reconciled.review_required)

    async def test_matching_evidence_confirms(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            tms.simulate_final_booking("LD1", expose_identity=True)
            reconciled = await service.reconcile(booking.id)
        self.assertIs(reconciled.state, State.CONFIRMED)
        self.assertEqual(reconciled.reference, booking.reference)

    async def test_mismatched_evidence_does_not_confirm(self):
        for key, value in (("BOOKING_REF", "OTHER"), ("MC_NUM", "999"), ("AGREED_RATE", "1")):
            with self.subTest(key=key):
                async with FakeTMS([make_load("LD1")]) as tms:
                    service = self.service_for(tms)
                    booking = await request(service)
                    tms.bookings["LD1"][key] = value
                    tms.simulate_final_booking("LD1", expose_identity=True)
                    reconciled = await service.reconcile(booking.id)
                self.assertIs(reconciled.state, State.ACK_PENDING)
                self.assertTrue(reconciled.review_required)

    async def test_an_unexpected_status_is_flagged_and_polling_never_clears_it(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            tms.set_status("LD1", "OPEN")
            flagged = await service.reconcile(booking.id)
            self.assertTrue(flagged.review_required)
            tms.set_status("LD1", "PENDING")
            again = await service.reconcile(booking.id)
        self.assertTrue(again.review_required)
        self.assertIs(again.state, State.ACK_PENDING)

    async def test_reconcile_never_sends_and_survives_an_outage(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            service = self.service_for(tms)
            booking = await request(service)
            tms.inject(faults.PARTIAL, faults.PARTIAL, faults.PARTIAL)
            self.assertEqual(await service.reconcile(booking.id), booking)
            await service.reconcile(booking.id)
        self.assertEqual(len(tms.book_requests), 1)


class AgentViewTests(Base):
    async def test_the_agent_hears_the_same_for_pending_and_unknown(self):
        async with FakeTMS([make_load("LD1")]) as tms:
            booking = await request(self.service_for(tms))
        unknown = replace(booking, state=State.UNKNOWN)
        self.assertEqual(agent_view(booking), agent_view(unknown))
        self.assertEqual(agent_view(booking),
                         {"status": "senior_review", "agreed_rate": 2000})

    async def test_the_view_hides_internal_fields(self):
        async with FakeTMS([make_load("LD1", MAX_BUY="2345")]) as tms:
            booking = await request(self.service_for(tms))
        view = repr(agent_view(booking))
        for hidden in ("2345", booking.reference, "PENDING", "ACK_PENDING", booking.write_intent_id):
            self.assertNotIn(hidden, view)
        self.assertNotIn("2345", repr(booking))

    async def test_a_failed_booking_says_not_booked(self):
        async with FakeTMS([]) as tms:
            booking = await request(self.service_for(tms))
        self.assertEqual(agent_view(booking), {"status": "not_booked", "reason": "load_gone"})


class OfferTests(unittest.TestCase):
    now = datetime(2026, 11, 1, tzinfo=timezone.utc)

    def summary(self, load_id, **overrides):
        values = {"PICKUP_DT": "20261102080000", **overrides}
        return to_summary(make_load(load_id, **values))

    def test_only_explicitly_open_loads_are_offered(self):
        for status in ("PENDING", "BOOKED", "EXPIRED", ""):
            with self.subTest(status=status):
                self.assertEqual(
                    select_offers([self.summary("LD1", STATUS=status)], self.now), []
                )

    def test_past_or_unreadable_pickups_are_excluded(self):
        for pickup in ("20261031080000", "not-a-date"):
            with self.subTest(pickup=pickup):
                self.assertEqual(
                    select_offers([self.summary("LD1", PICKUP_DT=pickup)], self.now), []
                )

    def test_our_own_active_bookings_are_excluded(self):
        loads = [self.summary("LD1"), self.summary("LD2")]
        offers = select_offers(loads, self.now, blocked_ids=frozenset({"LD1"}))
        self.assertEqual([load.load_id for load in offers], ["LD2"])

    def test_matches_are_rechecked_locally(self):
        loads = [self.summary("LD1", EQTYPE="REEFER"), self.summary("LD2")]
        offers = select_offers(loads, self.now, equipment="DRY_VAN", origin_state="TX",
                               dest_state="GA")
        self.assertEqual([load.load_id for load in offers], ["LD2"])

    def test_ranked_by_pickup_and_limited(self):
        loads = [
            self.summary(f"LD{day}", PICKUP_DT=f"202611{day:02d}080000")
            for day in (9, 3, 7, 5, 4)
        ]
        offers = select_offers(loads, self.now)
        self.assertEqual([load.load_id for load in offers], ["LD3", "LD4", "LD5"])
        self.assertEqual(len(offers), MAX_OFFERS)


class MappingTests(unittest.TestCase):
    def test_dimensions_convert_from_feet_to_inches(self):
        self.assertEqual(to_load(make_load(DIMS="40ft x 8ft x 9ft")).dimensions, "480 x 96 x 108 in")

    def test_free_text_dimensions_stay_as_written(self):
        self.assertEqual(to_load(make_load(DIMS="48X40 STD PALLETS")).dimensions, "48X40 STD PALLETS")

    def test_the_ceiling_stays_out_of_repr(self):
        self.assertNotIn("7654", repr(to_load(make_load(MAX_BUY="7654"))))

    def test_unusable_numbers_become_none(self):
        for value in ("0", "abc", "12.5", ""):
            with self.subTest(value=value):
                self.assertIsNone(to_load(make_load(MAX_BUY=value)).max_rate)

    def test_blank_notes_stay_blank(self):
        self.assertEqual(to_load(make_load(NOTES="")).notes, "")

    def test_timestamps_are_read_as_utc(self):
        pickup = to_load(make_load(PICKUP_DT="20261031030801")).pickup_datetime
        self.assertEqual(pickup.utcoffset(), timedelta(0))
        self.assertEqual(pickup.hour, 3)


if __name__ == "__main__":
    unittest.main()
