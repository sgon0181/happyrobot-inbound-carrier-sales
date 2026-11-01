"""BookingStore on the physical Twin booking rows."""
from dataclasses import asdict,fields,replace
import time
from service.core.booking import (Booking,State,RepDecision,ACTIVE,BookingConflict,OperationConflict)

PROTECTED=frozenset({'LD01086','LD01082','LD01081','LD01075','LD01077',
                     'LD01023','LD01032','LD01036','LD01069'})


def encode(booking):
    row=asdict(booking);row['state']=booking.state.value;row['rep_decision']=booking.rep_decision.value
    return row


def decode(row):
    data={f.name:row[f.name] for f in fields(Booking) if f.name in row}
    data['state']=State(data['state']);data['rep_decision']=RepDecision(data['rep_decision'])
    return Booking(**data)


class TwinBookingStore:
    def __init__(self,repository,live=False):self.repository,self.live=repository,live
    async def create(self,booking,operation_id,fingerprint):
        def change(data):
            for row in data['bookings'].values():
                if self.live and row.get('write_intent_id') and row['load_id']==booking.load_id:
                    if row['call_id']==booking.call_id:return decode(row),False
                    raise BookingConflict('Previously reserved load cannot be resent in this campaign')
                if row['call_id']==booking.call_id and row.get('operation_id')==operation_id:
                    if row['fingerprint']!=fingerprint:raise OperationConflict('Changed booking operation')
                    return decode(row),False
                if State(row['state']) in ACTIVE and (row['load_id']==booking.load_id or row['call_id']==booking.call_id):
                    if row['call_id']==booking.call_id:return decode(row),False
                    raise BookingConflict('Load already claimed')
            if self.live and (booking.mc!='138328' or booking.load_id in PROTECTED):
                raise BookingConflict('Outside prototype live authorization')
            row=encode(booking)
            cohort=data['calls'].get(booking.call_id,{}).get('cohort','real' if self.live else 'synthetic')
            row.update(operation_id=operation_id,fingerprint=fingerprint,cohort=cohort,
                       created_at=time.time())
            data['bookings'][booking.id]=row
            return booking,True
        return await self.repository.update(change)
    async def update(self,booking_id,expected,**changes):
        def change(data):
            row=data['bookings'][booking_id];booking=decode(row)
            if booking.state not in expected:return None
            if 'rep_decision' in changes and booking.rep_decision not in {RepDecision.AWAITING,changes['rep_decision']}:
                raise ValueError('The rep has already decided.')
            if changes.get('rep_decision') is RepDecision.CONFIRMED and booking.reason=='caller_confirmation_review':
                raise ValueError('Caller consent requires review.')
            if self.live and changes.get('state') is State.SUBMITTING:
                sends=[b for b in data['bookings'].values() if b.get('write_intent_id') and b.get('cohort')=='real']
                if len(sends)>=3 or any(b['state'] in {'ACK_PENDING','CONFIRMED'} and b.get('reference') for b in sends):
                    raise BookingConflict('Prototype live send gate closed')
            updated=replace(booking,**changes)
            row.update(encode(updated),updated_at=time.time())
            return updated
        return await self.repository.update(change)
    async def get(self,booking_id):
        _,data=await self.repository.read();return decode(data['bookings'][booking_id])
    async def in_states(self,states):
        _,data=await self.repository.read()
        return [decode(row) for row in data['bookings'].values() if State(row['state']) in states]
    async def blocked_load_ids(self):
        _,data=await self.repository.read()
        return frozenset(row['load_id'] for row in data['bookings'].values()
                         if State(row['state']) in ACTIVE or (self.live and row.get('write_intent_id')))
