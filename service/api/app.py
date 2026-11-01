"""Single instance API. All business state is in Production Twin."""
import asyncio
from contextlib import asynccontextmanager,suppress
import hmac
import json
import re
import time
import uuid
from types import SimpleNamespace
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from service.config import settings
from service.adapters.tms.client import TmsClient,TmsSettings
from service.adapters.tms.evidence import ReceiptJournal
from service.adapters.fmcsa.client import FMCSAClient
from service.adapters.notify.email import EmailNotifier
from service.adapters.twin.client import Platform
from service.adapters.twin.repository import TwinRepository
from service.core.calls import Runtime
from service.core.booking import agent_view


def redact_transcript(messages):
    """Redact literal and spoken six-digit codes, including failed attempts."""
    lines=[];tools=[]
    words=r'(?:zero|oh|one|two|three|four|five|six|seven|eight|nine)'
    for message in messages:
        for tool in message.get('tool_calls') or []:
            name=tool.get('name') or (tool.get('function') or {}).get('name')
            if name:tools.append(name)
        if message.get('role') not in ('user','assistant'):continue
        text=message.get('content')
        if not isinstance(text,str) or not text or text.startswith('<Thoughts>'):continue
        text=re.sub(r'\b[0-9]{6}\b','[code redacted]',text)
        text=re.sub(r'\b'+words+r'(?:[\s,-]+'+words+r'){5}\b','[spoken code redacted]',text,flags=re.I)
        text=re.sub(r'(?<!\d)(?:\d[ ,.-]){5}\d(?!\d)','[code redacted]',text)
        lines.append(message['role']+': '+text)
    return '\n'.join(lines),tools


def make_app(runtime,values,platform=None):
    async def collect():
        if platform is None:return {'status':'unavailable','collected':0}
        _,state=await runtime.repository.read();collected={}
        for cid,call in list(state['calls'].items())[-40:]:
            if not call.get('closed_at') or cid in state['call_transcripts'] or call['cohort']!='real':continue
            try:
                run=await asyncio.to_thread(platform.request,'/runs/'+cid)
                if run.get('workflow_id')!=values.get('PROTOTYPE_WORKFLOW_ID'):continue
                sessions=await asyncio.to_thread(platform.request,'/runs/'+cid+'/sessions')
                all_messages=[];complete=True
                for session in sessions.get('data',[]):
                    cursor=None
                    for _ in range(30):
                        suffix=('?cursor='+cursor) if cursor else ''
                        response=await asyncio.to_thread(platform.request,'/sessions/'+session['id']+'/messages'+suffix)
                        all_messages.extend(response.get('data',[]))
                        cursor=response.get('next_cursor') or (response.get('pagination') or {}).get('next_cursor')
                        if not cursor:break
                    else:complete=False
                text,tools=redact_transcript(all_messages)
                if text:
                    collected[cid]={'call_id':cid,'transcript':text,'tools':tools,'complete':complete,
                        'summary':'Recorded outcome: '+str(call.get('outcome')),
                        'summary_source':'DETERMINISTIC_PROTOTYPE','notes':'Live platform transcript, codes redacted.',
                        'sentiment':'not_assessed','source':'LIVE_PLATFORM_TRANSCRIPT'}
            except Exception:continue
        def save(data):
            for cid,row in collected.items():data['call_transcripts'][cid]=row
            return {'status':'ok','collected':len(collected)}
        return await runtime.repository.update(save)

    @asynccontextmanager
    async def lifespan(app):
        # Provisioning is an explicit setup command. Runtime never attempts DDL.
        await runtime.repository.read()
        await runtime.bookings.recover()
        async def sweep():
            while True:
                await asyncio.sleep(45)
                try:
                    _,data=await runtime.repository.read()
                    for cid,call in data['calls'].items():
                        if not call.get('closed_at') and time.time()-call['last_activity']>=1800:await runtime.close(cid)
                    await collect()
                except Exception:pass
        task=asyncio.create_task(sweep())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):await task
        if runtime.bookings.pending:await asyncio.gather(*runtime.bookings.pending,return_exceptions=True)

    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
    @app.middleware('http')
    async def protect(request,call_next):
        started=time.monotonic()
        ops=(request.url.path.startswith('/ops/') or (request.url.path.startswith('/bookings') and
             (request.method=='GET' or re.fullmatch(r'/bookings/[^/]+/(confirm|decline|reconcile)',request.url.path))))
        expected=values['OPS_API_KEY' if ops else 'AGENT_API_KEY']
        if not hmac.compare_digest(request.headers.get('authorization','').encode(),('Bearer '+expected).encode()):
            return JSONResponse({'status':'unauthorized'},401)
        try:
            if int(request.headers.get('content-length','0'))>16384:return JSONResponse({'status':'request_too_large'},413)
        except ValueError:return JSONResponse({'status':'invalid_request'},400)
        request.state.deadline=asyncio.get_running_loop().time()+12
        try:
            async with asyncio.timeout(12):response=await call_next(request)
        except TimeoutError:
            response=JSONResponse({'status':'in_progress' if request.url.path=='/bookings' else 'temporarily_unavailable'})
        response.headers['Cache-Control']='no-store'
        response.headers['X-Service-Duration-Ms']=str(round((time.monotonic()-started)*1000,1))
        return response
    @app.exception_handler(ValueError)
    @app.exception_handler(KeyError)
    async def invalid(request,error):return JSONResponse({'status':'invalid_request'},400)

    async def body(request):
        raw=await request.body()
        if len(raw)>16384:raise ValueError('Request too large')
        data=json.loads(raw)
        if not isinstance(data,dict):raise ValueError('JSON object required')
        return data
    def identity(data):
        cid=data['run_id']
        if not isinstance(cid,str) or str(uuid.UUID(cid))!=cid.lower():raise ValueError('Runtime run ID required')
        if any(key in data for key in ('call_id','call_token','operation_id','verified','eligible','max_rate')):
            raise ValueError('Untrusted state field')
        return cid
    async def execute(request,action):
        data=await body(request);cid=identity(data)
        lock=runtime.locks.setdefault(cid,asyncio.Lock())
        async with lock:
            try:return await action(cid,data)
            except (KeyError,ValueError):raise
            except Exception:return {'status':'temporarily_unavailable'}
    @app.get('/health')
    async def health():
        try:await runtime.tms.echo();return {'status':'ok','store':runtime.repository.label,'booking_enabled':runtime.tms.booking_enabled}
        except Exception:return {'status':'tms_unavailable'}
    @app.post('/carriers/verify')
    async def carrier(request:Request):return await execute(request,lambda cid,b:runtime.verify_carrier(cid,b['mc']))
    @app.post('/otp/send')
    async def send(request:Request):return await execute(request,lambda cid,b:runtime.send_code(cid))
    @app.post('/otp/verify')
    async def verify(request:Request):return await execute(request,lambda cid,b:runtime.verify_code(cid,b['code']))
    @app.post('/loads/search')
    async def search(request:Request):
        return await execute(request,lambda cid,b:runtime.search(cid,{k:b[k] for k in
            ('equipment','origin_state','dest_state','origin_city','pickup_date') if b.get(k)}))
    @app.post('/negotiate')
    async def negotiate(request:Request):
        return await execute(request,lambda cid,b:runtime.negotiate(cid,b['load_id'],b['rate']))
    @app.post('/bookings')
    async def book(request:Request):
        data=await body(request)
        if any(k in data for k in ('rate','mc','load_id')):raise ValueError('Booking uses stored agreement')
        return await execute(request,lambda cid,b:runtime.book(cid,request.state.deadline))
    @app.post('/calls/{cid}/close')
    async def close(cid:str,request:Request):
        data=await body(request)
        if identity(data)!=cid:raise ValueError('Run ID mismatch')
        return await runtime.close(cid)
    @app.get('/bookings')
    async def bookings():return {'status':'ok','bookings':(await runtime.snapshot())['queue']}
    @app.get('/ops/snapshot')
    async def snapshot():return await runtime.snapshot()
    @app.post('/bookings/{bid}/{action}')
    async def rep(bid:str,action:str,request:Request):
        if action not in ('confirm','decline','reconcile'):raise ValueError('Unknown action')
        data=await body(request)
        actor=data.get('actor')
        if not isinstance(actor,str) or not actor.strip() or len(actor)>200:raise ValueError('Signed-in rep required')
        booking=await (runtime.bookings.reconcile(bid) if action=='reconcile' else
                       getattr(runtime.bookings,action)(bid,actor))
        def audit(state):
            runtime.event(state,booking.call_id,'rep_'+action,booking.state.value,actor=actor,booking_id=bid)
        await runtime.repository.update(audit)
        return {'status':'ok','state':booking.state.value,'rep_decision':booking.rep_decision.value}
    @app.post('/ops/collect-transcripts')
    async def transcripts():return await collect()
    @app.post('/ops/fmcsa-probe')
    async def authority(request:Request):
        data=await body(request)
        try:return await runtime.authority(str(data.get('mc','138328')))
        except Exception:return {'status':'fmcsa_unavailable'}
    @app.post('/ops/calls/{cid}/qa')
    async def mark_qa(cid:str):
        if str(uuid.UUID(cid))!=cid.lower():raise ValueError('Run ID required')
        def change(data):
            call=data['calls'].setdefault(cid,runtime.new_call(cid))
            call.update(cohort='synthetic',qa_source='HYBRID_INTEGRATION_CHECK')
            for booking in data['bookings'].values():
                if booking['call_id']==cid:booking['cohort']='synthetic'
            return {'status':'ok'}
        return await runtime.repository.update(change)
    app.state.runtime=runtime
    return app


def configured_app():
    values=settings()
    for key in ('AGENT_API_KEY','OPS_API_KEY','OTP_HASH_SECRET','PRICING_SECRET'):
        if len(values.get(key,''))<24:raise RuntimeError('Private service configuration required')
    platform=Platform(values);repository=TwinRepository(platform,values.get('TWIN_TABLE_PREFIX','proto_'))
    tms=TmsClient(TmsSettings(values['TMS_HOST'],int(values['TMS_PORT']),values['TMS_TOKEN'],
                              booking_enabled=values.get('BOOKING_ENABLED')=='true'),
                  ReceiptJournal(values.get('RECEIPT_JOURNAL_DIR','/tmp/carrier-receipts')))
    fmcsa=FMCSAClient(SimpleNamespace(fmcsa_api_key=values['FMCSA_API_KEY'],timeout=5))
    async def authority(mc):
        record=await asyncio.to_thread(fmcsa.lookup,mc);record['source']='LIVE_FMCSA';return record
    runtime=Runtime(repository,tms,authority,EmailNotifier(values,platform),values)
    return make_app(runtime,values,platform)


if __name__=='__main__':
    import uvicorn
    uvicorn.run(configured_app(),host='0.0.0.0',port=8767,access_log=False)
