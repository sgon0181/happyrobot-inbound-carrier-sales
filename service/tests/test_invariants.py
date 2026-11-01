"""Regression checks for the prototype's durable guards."""
import asyncio
from dataclasses import replace
import time
import unittest
from service.adapters.twin.repository import TwinRepository,MemoryRepository
from service.adapters.twin.bookings import TwinBookingStore
from service.core.booking import Booking,BookingService,State,RepDecision,BookingConflict
from service.core.ports import BookingOutcome,BookingReceipt
from service.adapters.tms.mapping import to_load
from service.adapters.tms.fake import make_load


class Guards(unittest.IsolatedAsyncioTestCase):
    async def test_corrupt_nonempty_canonical_state_fails_closed(self):
        class Client:
            async def sql(self,sql):return {'rows':[{'version':3,'data':{'calls':{}}}]}
        with self.assertRaises(RuntimeError):await TwinRepository(Client()).read()

    async def test_spent_failed_load_cannot_be_reserved_again(self):
        repo=MemoryRepository();store=TwinBookingStore(repo,live=True)
        old=Booking('old','call-a','FRESH-LD','138328',1000,'a',state=State.FAILED,write_intent_id='sent')
        repo.data['bookings'][old.id]={**old.__dict__,'state':old.state.value,
            'rep_decision':'awaiting','cohort':'real'}
        self.assertIn('FRESH-LD',await store.blocked_load_ids())
        with self.assertRaises(BookingConflict):
            await store.create(Booking('new','call-b','FRESH-LD','138328',1000,'b'),'b','b')

    async def test_rep_decisions_compete_atomically(self):
        repo=MemoryRepository();store=TwinBookingStore(repo)
        b=Booking('booking','call','load','138328',1000,'a',state=State.ACK_PENDING,reference='ref')
        await store.create(b,'op','fp')
        results=await asyncio.gather(store.update(b.id,frozenset({State.ACK_PENDING}),rep_decision=RepDecision.CONFIRMED),
            store.update(b.id,frozenset({State.ACK_PENDING}),rep_decision=RepDecision.DECLINED),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,ValueError) for r in results),1)

    async def test_slow_intent_save_never_starts_send_after_deadline(self):
        repo=MemoryRepository();store=TwinBookingStore(repo);calls=[]
        class TMS:
            booking_enabled=True
            async def get(self,id):return to_load(make_load(id))
            async def book(self,*args):calls.append(args);return BookingReceipt(BookingOutcome.ACK_PENDING,'r','PENDING')
        original=store.update
        async def slow(id,expected,**changes):
            result=await original(id,expected,**changes)
            if changes.get('state') is State.SUBMITTING:await asyncio.sleep(1.1)
            return result
        store.update=slow;service=BookingService(store,TMS())
        deadline=asyncio.get_running_loop().time()+6.05
        result=await service.request(call_id='call',operation_id='op',load_id='load',mc='138328',rate=1000,
                                     agreement_version='a',deadline=deadline)
        self.assertEqual(calls,[]);self.assertIs(result.state,State.FAILED)
