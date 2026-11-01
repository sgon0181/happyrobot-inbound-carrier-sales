"""Row contention and fail-closed crash gaps, with no external connections."""

import asyncio
import unittest
from dataclasses import replace

from service.adapters.twin.repository import MemoryRepository, CONTROL
from service.adapters.twin.bookings import TwinBookingStore
from service.core.booking import Booking, BookingConflict, State


class EntityStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_eight_load_contenders_have_one_winner(self):
        repository = MemoryRepository()
        store = TwinBookingStore(repository)

        async def claim(i):
            try:
                return await store.create(
                    Booking(str(i), "call" + str(i), "load", "123456", 1000, "a"), "op", "fp"
                )
            except BookingConflict:
                return None

        results = await asyncio.gather(*(claim(i) for i in range(8)))
        self.assertEqual(sum(bool(r and r[1]) for r in results), 1)

    async def test_booking_row_conditional_transition_has_one_winner(self):
        repository = MemoryRepository()
        store = TwinBookingStore(repository)
        await store.create(Booking("b", "call", "load", "123456", 1000, "a"), "op", "fp")
        results = await asyncio.gather(
            *(store.update("b", {State.AGREED}, state=State.UNKNOWN) for _ in range(8))
        )
        self.assertEqual(sum(r is not None for r in results), 1)

    async def test_otp_consumption_is_a_separate_single_winner_cas(self):
        repository = MemoryRepository()
        await repository.cas("otp_challenges", "otp", None, {"consumed_at": None})

        def consume(row):
            if row["consumed_at"]:
                return False
            row["consumed_at"] = 123
            return True

        results = await asyncio.gather(
            *(repository.mutate("otp_challenges", "otp", consume) for _ in range(8))
        )
        self.assertEqual(sum(results), 1)

    async def test_partial_reservation_blocks_instead_of_being_stolen(self):
        repository = MemoryRepository()
        store = TwinBookingStore(repository)
        original = repository.cas

        async def crash(table, key, version, row):
            if table == "bookings":
                raise RuntimeError("simulated crash before booking insert")
            return await original(table, key, version, row)

        repository.cas = crash
        with self.assertRaises(RuntimeError):
            await store.create(Booking("b", "call", "load", "123456", 1000, "a"), "op", "fp")
        repository.cas = original
        self.assertIn("load", await store.blocked_load_ids(["load"]))
        with self.assertRaises(BookingConflict):
            await store.create(Booking("b2", "call", "load", "123456", 1000, "a"), "op", "fp")

    async def test_only_failed_without_intent_releases_claims(self):
        repository = MemoryRepository()
        store = TwinBookingStore(repository)
        await store.create(Booking("b", "call", "load", "123456", 1000, "a"), "op", "fp")
        await store.update("b", {State.AGREED}, state=State.FAILED)
        self.assertNotIn("load", await store.blocked_load_ids(["load"]))
        await store.create(Booking("b2", "call2", "load", "123456", 1000, "a"), "op", "fp")
        await store.update("b2", {State.AGREED}, state=State.SUBMITTING, write_intent_id="intent")
        await store.update("b2", {State.SUBMITTING}, state=State.FAILED)
        self.assertIn("load", await store.blocked_load_ids(["load"]))

    async def test_different_calls_do_not_wait_for_another_calls_cas(self):
        repository = MemoryRepository()
        original = repository.cas
        entered, release = asyncio.Event(), asyncio.Event()

        async def delayed(table, key, version, row):
            if table == "calls" and key == "slow":
                entered.set()
                await release.wait()
            return await original(table, key, version, row)

        repository.cas = delayed

        def change(data, call):
            call["counter"] = 1

        slow = asyncio.create_task(repository.update_call("slow", change, {"id": "slow"}))
        await entered.wait()
        await asyncio.wait_for(repository.update_call("fast", change, {"id": "fast"}), 0.1)
        release.set()
        await slow
        self.assertEqual(repository.data["calls"]["fast"]["counter"], 1)

    async def test_control_row_excluded_from_all_entity_views(self):
        repository = MemoryRepository()
        repository.data["calls"][CONTROL] = {"calls": {"old": "frozen"}}
        _, state = await repository.read()
        self.assertNotIn(CONTROL, state["calls"])

    async def test_call_is_unfrozen_before_its_claim_becomes_reusable(self):
        repository = MemoryRepository()
        await repository.cas("calls", "call", None, {"id": "call", "agreement": None})
        store = TwinBookingStore(repository)
        await store.create(Booking("b", "call", "load", "123456", 1000, "a"), "op", "fp")
        original = repository.cas

        async def inspect_release(table, key, version, row):
            if table == "booking_claims" and key == "call:call" and not row.get("active"):
                self.assertNotIn("booking_id", repository.data["calls"]["call"])
                self.assertFalse(repository.data["booking_claims"]["load:load"]["active"])
            return await original(table, key, version, row)

        repository.cas = inspect_release
        await store.update("b", {State.AGREED}, state=State.FAILED)
        result, created = await store.create(
            Booking("b2", "call", "load2", "123456", 1000, "b"), "op2", "fp2"
        )
        self.assertTrue(created)
        self.assertEqual(result.id, "b2")

    async def test_failed_operation_is_still_idempotent_after_claim_release(self):
        repository = MemoryRepository()
        store = TwinBookingStore(repository)
        booking = Booking("b", "call", "load", "123456", 1000, "a")
        await store.create(booking, "operation", "fingerprint")
        await store.update("b", {State.AGREED}, state=State.FAILED)
        again, created = await store.create(replace(booking, id="new"), "operation", "fingerprint")
        self.assertFalse(created)
        self.assertEqual(again.id, "b")
        self.assertIs(again.state, State.FAILED)
