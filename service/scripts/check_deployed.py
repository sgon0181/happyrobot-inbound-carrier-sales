"""HYBRID deployed path: real integrations, explicitly synthetic OTP proof.

Booking must be disabled. This is not a human email-code verification or voice
call, and never claims either. The one synthetic call is labelled before use.
"""
import asyncio
import hashlib
import hmac
import json
from pathlib import Path
import time
import uuid
import httpx
from service.config import settings,ROOT
from service.adapters.twin.client import Platform
from service.adapters.twin.repository import TwinRepository


async def main():
    values=settings();base='https://codex-e2e-lab-sg-20261031.fly.dev'
    cid=str(uuid.uuid4());checks=[]
    async with httpx.AsyncClient(base_url=base,timeout=16) as client:
        async def call(path,body=None,ops=False):
            started=time.monotonic()
            headers={'Authorization':'Bearer '+values['OPS_API_KEY' if ops else 'AGENT_API_KEY']}
            response=await (client.get(path,headers=headers) if body is None else client.post(path,headers=headers,json=body))
            response.raise_for_status();result=response.json()
            checks.append({'path':path,'status':result.get('status'),'http':response.status_code,
                           'client_ms':round((time.monotonic()-started)*1000,1),
                           'service_ms':response.headers.get('X-Service-Duration-Ms')})
            return result
        health=await call('/health');assert health['booking_enabled'] is False
        await call('/ops/calls/'+cid+'/qa',{},True)
        auth=await call('/carriers/verify',{'run_id':cid,'mc':'138328'});assert auth['status']=='ok'
        delivery=await call('/otp/send',{'run_id':cid})
        # Explicit synthetic verification fixture, scoped to this QA call only.
        # No production endpoint exists for changing verification state.
        repo=TwinRepository(Platform(values));code='000001'
        digest=hmac.new(values['OTP_HASH_SECRET'].encode(),(cid+'|138328|'+code).encode(),hashlib.sha256).hexdigest()
        def fixture(data):
            call=data['calls'][cid]
            assert call['cohort']=='synthetic' and not call.get('code_passed_at')
            challenge=data['otp_challenges'][call['challenge']]
            challenge.update(hash=digest,delivery_status='sent',proof_source='SIMULATED_QA_CODE')
        await repo.update(fixture)
        verified=await call('/otp/verify',{'run_id':cid,'code':code});assert verified['code_passed']
        loads=await call('/loads/search',{'run_id':cid,'equipment':'DRY_VAN','origin_state':'MA','dest_state':'OH'})
        assert loads['status']=='ok' and loads['loads']
        load=loads['loads'][0]
        counter=await call('/negotiate',{'run_id':cid,'load_id':load['load_id'],'rate':str(load['offer']+25)})
        if counter['status']=='counter':
            agreed=await call('/negotiate',{'run_id':cid,'load_id':load['load_id'],'rate':str(counter['offer'])})
        else:agreed=counter
        assert agreed['status']=='agreed'
        booking=await call('/bookings',{'run_id':cid})
        assert booking['status']=='not_booked' and booking['reason']=='live_booking_disabled'
        await call('/calls/'+cid+'/close',{'run_id':cid})
        _,data=await repo.read()
        rows=[b for b in data['bookings'].values() if b['call_id']==cid]
        assert all(not b.get('write_intent_id') for b in rows)
        if repo.pending:await asyncio.gather(*repo.pending)
        result={'label':'HYBRID','run_id':cid,'authority':'LIVE_FMCSA','notification':delivery['status'],
            'otp_proof':'SIMULATED_QA_CODE','loads':'LIVE_TMS','selected_load':load['load_id'],
            'opening':load['offer'],'counter':counter,'booking_status':booking['status'],
            'live_sends':0,'checks':checks}
        (ROOT/'secrets/deployed-flow-off.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))


if __name__=='__main__':asyncio.run(main())
