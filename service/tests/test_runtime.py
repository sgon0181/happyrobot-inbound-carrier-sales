"""SIMULATED API and policy tests. The package guard blocks external traffic."""
import asyncio
from dataclasses import replace
import json
import unittest
import uuid
from unittest.mock import patch
import httpx
from service.adapters.tms.fake import FakeTMS,make_load
from service.adapters.twin.repository import MemoryRepository
from service.adapters.twin.bookings import TwinBookingStore
from service.api.app import make_app,redact_transcript
from service.core.calls import Runtime
from service.core.booking import Booking,State,BookingService,agent_view
from service.tests.support import client_for

VALUES={key:'synthetic-'+key+'-01234567890123456789' for key in
        ('AGENT_API_KEY','OPS_API_KEY','OTP_HASH_SECRET','PRICING_SECRET')}
VALUES['DEMO_OTP_EMAIL']='demo@example.invalid'


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server=FakeTMS([make_load('LD1')]);await self.server.__aenter__()
        self.repository=MemoryRepository();self.sent=[];self.now=1000
        async def authority(mc):return {'eligible':mc=='138328','reason':'active','carrier':{'legalName':'Synthetic Carrier'}}
        async def notify(code,cid):self.sent.append((code,cid));return {'sent':True,'source':'SIMULATED'}
        self.runtime=Runtime(self.repository,client_for(self.server),authority,notify,VALUES,clock=lambda:self.now)
        self.cid=str(uuid.uuid4())
        self.http=httpx.AsyncClient(transport=httpx.ASGITransport(app=make_app(self.runtime,VALUES)),base_url='http://local')
        self.agent={'Authorization':'Bearer '+VALUES['AGENT_API_KEY']}
        self.ops={'Authorization':'Bearer '+VALUES['OPS_API_KEY']}
    async def asyncTearDown(self):
        await self.http.aclose();await self.server.__aexit__(None,None,None)
    async def ready(self):
        await self.runtime.verify_carrier(self.cid,'138328');await self.runtime.send_code(self.cid)
        await self.runtime.verify_code(self.cid,self.sent[-1][0])
        return await self.runtime.search(self.cid,{'equipment':'DRY_VAN'})

    async def test_all_routes_require_auth_and_roles_are_separate(self):
        for method,path in [('GET','/health'),('GET','/ops/snapshot'),('GET','/bookings'),
                            ('POST','/otp/send'),('POST','/bookings'),('GET','/docs'),('GET','/openapi.json')]:
            self.assertEqual((await self.http.request(method,path)).status_code,401)
        self.assertEqual((await self.http.get('/ops/snapshot',headers=self.agent)).status_code,401)
        self.assertEqual((await self.http.post('/otp/send',headers=self.ops,json={'run_id':self.cid})).status_code,401)

    async def test_search_requires_authority_and_code_and_hides_ceiling(self):
        self.assertEqual((await self.runtime.search(self.cid,{}))['status'],'carrier_ineligible')
        await self.runtime.verify_carrier(self.cid,'138328')
        self.assertEqual((await self.runtime.search(self.cid,{}))['status'],'otp_required')
        result=await self.ready()
        self.assertEqual(result['status'],'ok')
        self.assertNotIn('max_rate',json.dumps(result));self.assertNotIn('loadboard_rate',json.dumps(result))

    async def test_code_is_call_bound_consumed_and_never_returned(self):
        await self.runtime.verify_carrier(self.cid,'138328');result=await self.runtime.send_code(self.cid)
        code=self.sent[-1][0]
        self.assertNotIn(code,json.dumps(result));self.assertNotIn(code,json.dumps(self.repository.data))
        other=str(uuid.uuid4());await self.runtime.verify_carrier(other,'138328')
        self.assertEqual((await self.runtime.verify_code(other,code))['status'],'code_expired_or_used')
        result=await self.runtime.verify_code(self.cid,code);self.assertTrue(result['code_passed'])
        self.now+=6
        self.assertEqual((await self.runtime.verify_code(self.cid,code))['status'],'code_expired_or_used')

    async def test_resends_do_not_reset_failed_code_budget_or_authorize_alternate_contact(self):
        await self.runtime.verify_carrier(self.cid,'138328');await self.runtime.send_code(self.cid)
        for _ in range(2):
            await self.runtime.verify_code(self.cid,'not-the-code');self.now+=6
        await self.runtime.send_code(self.cid)
        self.assertEqual((await self.runtime.verify_code(self.cid,'not-the-code'))['status'],'code_failed')
        self.now+=6
        self.assertEqual((await self.runtime.send_code(self.cid))['status'],'code_failed')

    async def test_same_counter_inside_window_is_retry_then_consumes_round(self):
        await self.ready()
        first=await self.runtime.negotiate(self.cid,'LD1','99999')
        again=await self.runtime.negotiate(self.cid,'LD1','99999')
        self.assertEqual(first,again);self.assertEqual(self.repository.data['calls'][self.cid]['rounds'],1)
        self.now+=6;await self.runtime.negotiate(self.cid,'LD1','99999')
        self.assertEqual(self.repository.data['calls'][self.cid]['rounds'],2)
        self.now+=6;await self.runtime.negotiate(self.cid,'LD1','99999')
        self.now+=6;result=await self.runtime.negotiate(self.cid,'LD1','99999')
        self.assertEqual(result['status'],'negotiation_failed')
        self.assertEqual((await self.runtime.book(self.cid,None))['status'],'agreement_required')

    async def test_booking_uses_stored_rate_and_does_not_resend(self):
        result=await self.ready();offer=result['loads'][0]['offer']
        await self.runtime.negotiate(self.cid,'LD1',str(offer))
        first=await self.runtime.book(self.cid,None);again=await self.runtime.book(self.cid,None)
        self.assertEqual(first,again);self.assertEqual(first['status'],'senior_review')
        self.assertEqual(len(self.server.book_requests),1)
        self.assertNotIn('reference',json.dumps(first))

    async def test_repeated_acceptance_tracks_the_latest_selected_load(self):
        self.server.board['LD2']=make_load('LD2')
        result=await self.ready();offers={x['load_id']:x['offer'] for x in result['loads']}
        await self.runtime.negotiate(self.cid,'LD1',str(offers['LD1']))
        await self.runtime.negotiate(self.cid,'LD2',str(offers['LD2']))
        again=await self.runtime.negotiate(self.cid,'LD1',str(offers['LD1']))
        self.assertEqual(again['load_id'],'LD1')
        self.assertEqual(self.repository.data['calls'][self.cid]['agreement']['load_id'],'LD1')

    async def test_no_confirm_on_unknown(self):
        store=TwinBookingStore(self.repository)
        b=Booking('unknown',self.cid,'LD1','138328',1000,'agreement',state=State.UNKNOWN)
        await store.create(b,'operation','fingerprint')
        with self.assertRaises(ValueError):await BookingService(store,self.runtime.tms).confirm(b.id,'rep')
        self.assertEqual(len(self.server.book_requests),0)

    async def test_hidden_identity_rejects_injected_call_fields(self):
        for key in ('call_id','call_token','verified','max_rate'):
            result=await self.http.post('/carriers/verify',headers=self.agent,
                                       json={'run_id':self.cid,'mc':'138328',key:'injected'})
            self.assertEqual(result.status_code,400)

    async def test_early_hangup_is_stored(self):
        result=await self.runtime.close(self.cid)
        self.assertEqual(result['outcome'],'caller_ended')
        self.assertIsNotNone(self.repository.data['calls'][self.cid]['closed_at'])

    async def test_transcript_redaction_preserves_lane_and_handles_failed_spoken_codes(self):
        text,_=redact_transcript([{'role':'user','content':'My code is zero one two three four five, Texas to New Jersey.'},
                                 {'role':'user','content':'Wrong code 123456. Try 9 8 7 6 5 4.'}])
        for hidden in ('123456','zero one two three four five','9 8 7 6 5 4'):self.assertNotIn(hidden,text)
        self.assertIn('Texas to New Jersey',text)
