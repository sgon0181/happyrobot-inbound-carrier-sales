"""Build three source-linked caller diagrams. Documentation only, no service imports."""
from pathlib import Path
import json
from pypdf import PdfReader, PdfWriter
from rendering import Page, C, OUT, PAGES

HERE = Path(__file__).resolve().parent
from reportlab.pdfbase.pdfmetrics import stringWidth

STEPS = [
 dict(id='C1',title='Identify myself',build='B2',say='Open web call.\n"MC 138328."',hear='Greeting / MC request; then: "Synthetic Carrier LLC, right?"',
      hr='Transcribe MC; choose verify_carrier.',tool='verify_carrier(mc)',route='/carriers/verify',
      decide='Normalize MC; select it before lookup; assess active authority. Only latest lookup can apply.',
      data='{run_id, mc}\nFMCSA records -> Authority\nReply: eligible + name',contacts='FMCSA HTTP lookup',
      state='new calls[run_id]\nmc, lookup, carrier_name,\neligible, authority\n+ checking/result events',
      code=['calls.py: Calls.verify_carrier [B2]','core/carrier_policy.py: normalize_mc, assess [B2]','adapters/fmcsa.py: Fmcsa.carriers [B2]']),
 dict(id='C2',title='Confirm + get code',build='B2',say='"Yes, that is us."\nOpen configured demo inbox.',hear='"A six-digit code was emailed. Please read it back."',
      hr='Name Yes is prompt-only; then send_code. No backend confirmation flag.',tool='send_code()',route='/otp/send',
      decide='Require eligibility. Generate code; save hash, expiry and send budget before SMTP. Record SMTP result.',
      data='{run_id}\ncode -> CodeState(hash)\nReply: sent (SMTP accepted)',contacts='Gmail SMTP -> demo inbox',
      state='calls[run_id].otp\nhash, expiry, sends, failed\n+ code_issued / sent events',
      code=['calls.py: Calls.send_code [B2]','core/codes.py: new_code, code_hash, issue [B2]','adapters/email.py: CodeMailer.send [B2]']),
 dict(id='C3',title='Read back code',build='B2',say='Read [code] from inbox.\nSpeak its digits.',hear='"You are verified. What equipment and lane?"',
      hr='Digits enter HR records / request; verify_code returns status only.',tool='verify_code(code)',route='/otp/verify',
      decide='Normalize digits; compare keyed hash; check expiry/limits. Consume code and verify together.',
      data='{run_id, code}\nCodeState -> verified\nReply: verified',contacts='Twin only; no FMCSA or TMS read',
      state='calls[run_id]\notp.consumed_at\nverified_at + event\nCode digits not in events',
      code=['calls.py: Calls.verify_code [B2]','core/codes.py: normalize_code, check [B2]','calls.py: is_verified [B2]']),
 dict(id='C4',title='Ask for a load',build='B3',say='"Dry van, Texas to Georgia."',hear='LD90001: Dallas to Atlanta; pickup, cargo, $1,800. Does that work?',
      hr='Extract equipment and state codes; choose find_loads; speak returned public fields.',tool='find_loads(equipment, lane)',route='/loads/search',
      decide='Gate before TMS. Exclude held loads; pick up to 3 OPEN future loads. Price safely; recheck gate at write.',
      data='Search -> summaries / Load\nLoad + offer -> public dict\nReply: found + public loads',contacts='Twin holds; TMS QUERY + GET',
      state='calls[run_id]\nsearch, offers,\npolicy_version\n+ public pitch event\nNo ceiling or posted rate',
      code=['selling.py: find_loads, _open_loads [B3]','core/loads.py: select_offers, public_view [B1]','core/pricing.py: price_load [B1]']),
 dict(id='C5',title='Make a counter',build='B3',say='"I need $2,100."',hear='"I can do $1,900. Does that work?"',
      hr='Choose negotiate with the exact ask. Quote only service-approved counter.',tool='negotiate(load_id, rate)',route='/negotiate',
      decide='Fresh LOAD_GET + pricing. Decide in versioned call write; <=3 call-wide counters. Same last ask/load uses no round.',
      data='heard "2100" -> ask 2100\nLoad -> Terms -> Step\nReply: counter 1900, round 1',contacts='Fresh TMS GET; Twin decision',
      state='calls[run_id]\noffers, rounds=1,\nlast_counter\n+ heard / ask / reply event\nNo agreement yet',
      code=['selling.py: negotiate, _fresh_terms [B3]','sale_decisions.py: answer_counter [B3]','core/negotiation.py: respond [B1]']),
 dict(id='C6',title='Agree on the rate',build='B3',say='"Yes, $1,900 works."',hear='LD90001 agreed at $1,900. Senior rep will confirm (mocked handoff).',
      hr='Send acceptance to negotiate first. Only agreed permits the spoken mocked handoff.',tool='negotiate(load_id, rate)',route='/negotiate',
      decide='Fresh terms again. Claim one agreement per call; booking row decides the load holder; settle claim before replying.',
      data='Step: ACCEPT -> claim\nload snapshot -> RESERVED\nReply: agreed / 1900',contacts='TMS GET; 3 Twin row decisions',
      state='1 calls: accepting claim\n2 bookings: RESERVED\n   + rep snapshot / event\n3 calls: agreement\n   + clear claim / event\nNot one transaction',
      code=['sale_decisions.py: _apply, settle [B3]','bookings.py: Bookings.reserve [B3]','core/loads.py: reservation_view [B4]','Rep: posted; no ceiling.']),
 dict(id='C7',title='Finish the call',build='B3',say='"Thank you. Goodbye."\nEnd voice session.',hear='Courteous farewell.\nNo live transfer or final TMS booking.',
      hr='Choose close_call. Then V4 end webhook sends initiator / duration.',tool='close_call(summary) + callback',route='/calls/close\n/calls/ended (callback)',
      decide='First model close/notes stand. Separate end report is idempotent. Neither releases reservation nor sends booking.',
      data='summary -> closed\ninitiator + duration\n-> ended (if delivered)',contacts='Twin only; end capture if delivered',
      state='calls[run_id]\nclosed_at, summary + event\nended_at, ended_by\nduration_seconds\n+ end event if delivered\nHold remains RESERVED',
      code=['selling.py: Sales.close [B3]','calls.py: Calls.end [B2 module; later capture]','CallRows.step / Twin.change write state + event [B2]'])
]


def blueprint():
    p=Page('01-caller-blueprint','My call, end to end','Seven call moments mapped to speech, decisions, data, files and saved state.')
    p.common('1','Caller-centred blueprint','Read left to right. The same synthetic example and call IDs appear in the other two views.')
    left, label, cw=44,166,1426/7
    rows=[(309,116,'ME','What I do / hear','ink'),(425,110,'HAPPYROBOT','Managed conversation','hr'),(535,113,'SERVICE','Decision and purpose','svc'),(648,98,'DATA / CONTACT','Temporary values + I/O','data'),(746,158,'TWIN STATE','Saved, keyed records','data'),(904,174,'CODE / BUILD','Files + key functions','svc')]
    for y,h,title,subtitle,color in rows:
        p.rect(left,y,label,h,C['soft'],C['line']);p.text(left+13,y+28,title,14,C[color],'Helvetica-Bold');p.text(left+13,y+52,subtitle,13,C['muted'],width=label-26)
    for i,s in enumerate(STEPS):
        x=left+label+i*cw
        p.rect(x,255,cw,46,C['soft'],C['line']);p.badge(x+9,264,s['id']);p.text(x+49,282,s['title'],13.8,C['ink'],'Helvetica-Bold')
        for y,h,_,_,color in rows:p.rect(x,y,cw,h,C['paper'],C['line'])
        say_end=p.text(x+11,330,s['say'],14.1,C['ink'],width=cw-22,leading=17)
        p.text(x+11,max(373,say_end+3),'HEAR: '+s['hear'],13.7,C['muted'],width=cw-22,leading=16.1)
        p.text(x+11,446,s['tool'],12.8,C['hr'],'Courier',width=cw-22,leading=15)
        p.text(x+11,477,s['hr'],13.3,C['hr'],width=cw-22,leading=15.7)
        p.text(x+11,557,s['decide'],14,C['svc'],width=cw-22,leading=17.2)
        p.rect(x+8,657,cw-16,53,C['databg'],C['data'],8)
        p.text(x+15,674,s['data'],12.3,C['data'],width=cw-30,leading=14.4)
        p.text(x+11,727,s['contacts'],12.8,C['ext'],width=cw-22,leading=15)
        p.store(x+9,756,cw-18,138,'SAVED',s['state'],12.8)
        p.badge(x+11,914,s['build'],'build');p.text(x+63,933,'owns this step',12,C['muted'])
        yy=960
        for code in s['code']:
            end=p.text(x+11,yy,code,12.5,C['svc'],width=cw-22,leading=15)
            yy=end+3
        if yy>1078:p.issues.append(f'Code cell {s["id"]}: {yy}')
    p.rect(44,1091,1592,65,C['soft'],C['muted'],8,True)
    p.text(60,1116,'SEPARATE REP PATH: B4 App reads Twin through Dashboard.snapshot(). A rep reviews the captured deal; Confirm is disabled while sends are off/unknown.',14,C['ink'],'Helvetica-Bold')
    p.text(60,1139,'Only RepActions.confirm() can send LOAD_BOOK, with mode/version/fresh-load checks. PENDING = ACK_PENDING, not BOOKED. No actual transfer is implemented.',13.5,C['muted'])
    p.footer();return p.issues


def sequence():
    p=Page('02-call-sequence','The order behind what I hear','Top-to-bottom sequence with service-owned decisions and explicit persistence boundaries.')
    p.common('2','Sequence: from my words to a saved reservation','Solid arrows are requests/actions; dashed arrows are replies or the conditional post-agent callback. Boxes at right locate the code.')
    actors=[(145,'ME','ink'),(395,'HAPPYROBOT','hr'),(725,'SERVICE','svc'),(1055,'FMCSA / EMAIL / TMS','ext'),(1300,'TWIN','data')]
    for x,title,key in actors:
        p.rect(x-92,260,184,33,C[key+'bg'] if key+'bg' in C else C['soft'],C[key],7);p.text(x-81,282,title,13.6,C[key],'Helvetica-Bold');p.line(x,298,x,1081,C['line'],1,True)
    p.text(1420,282,'FILES / KEY FUNCTIONS',13,C['svc'],'Helvetica-Bold')
    y=299
    def msg(a,b,dy,label,key='ink',reply=False):
        xx1,xx2=actors[a][0],actors[b][0]; yy=y+dy
        p.line(xx1,yy,xx2,yy,C[key],1.3,reply,True)
        p.text(min(xx1,xx2)+8,yy-4,label,12.1,C[key])
    def band(s,height,code):
        p.rect(44,y-3,1327,height-7,C['paper'],None,0)
        for x,_,_ in actors:p.line(x,y-10,x,y+height-10,C['line'],1,True)
        p.badge(53,y+1,s['id']);p.rect(1400,y-10,236,height-2,C['svcbg'],C['line'],7)
        p.badge(1410,y-2,s['build'],'build');p.text(1461,y+16,s['title'],12.6,C['svc'],'Helvetica-Bold')
        p.text(1412,y+39,code,12.2,C['svc'],width=210,leading=15)
    band(STEPS[0],124,'calls.py\nCalls.verify_carrier\ncore/carrier_policy.py: assess\nadapters/fmcsa.py: carriers')
    for args in [(0,1,8,'MC 138328'),(1,2,22,'POST /carriers/verify {run_id, mc}','hr'),(2,4,36,'save selected MC / lookup + checking event','data'),(2,3,50,'FMCSA HTTP: carriers(mc)','ext'),(3,2,64,'FMCSA carrier records','ext',True),(2,4,78,'assess -> save authority / eligible + event','data'),(2,1,92,'eligible + carrier_name','svc',True),(1,0,106,'"Synthetic Carrier LLC, right?"','hr',True)]:msg(*args)
    y+=124
    band(STEPS[1],124,'calls.py: send_code\ncore/codes.py: issue/hash\nadapters/email.py: send\nName Yes is prompt-only')
    for args in [(0,1,8,'"Yes."'),(1,2,22,'POST /otp/send {run_id}','hr'),(2,4,36,'save hash, expiry, send budget + event','data'),(2,3,50,'Gmail SMTP -> configured inbox [code]','ext'),(3,2,64,'SMTP accepted','ext',True),(2,4,78,'save sent event (not a read receipt)','data'),(2,1,92,'sent; expected code is not returned','svc',True),(1,0,106,'"Read the code from your inbox."','hr',True)]:msg(*args)
    y+=124
    band(STEPS[2],82,'calls.py: verify_code\ncore/codes.py: check\nConsume + verify in one row')
    for args in [(0,1,8,'Speak [code]'),(1,2,22,'POST /otp/verify {run_id, code}','hr'),(2,4,36,'check CodeState; consume + verified_at + event','data'),(2,1,50,'verified','svc',True),(1,0,64,'"Equipment and lane?"','hr',True)]:msg(*args)
    y+=82
    band(STEPS[3],152,'selling.py: find_loads\n_open_loads\ncore/loads.py\nselect_offers, public_view\ncore/pricing.py: price_load\nB1 rules + B3 flow')
    for args in [(0,1,8,'"Dry van, TX to GA."'),(1,2,22,'POST /loads/search {run_id, terms}','hr'),(2,3,36,'gate -> TMS TCP: LOAD_QUERY','ext'),(3,2,50,'LoadSummary records','ext',True),(2,4,64,'Bookings.held -> get_many (one IN query)','data'),(2,3,78,'TMS TCP: LOAD_GET for selected loads','ext'),(3,2,92,'raw load detail records','ext',True),(2,4,106,'filter + price -> save search / offers / pitch event','data'),(2,1,120,'found + public loads; no ceiling / posted rate','svc',True),(1,0,134,'Pitch LD90001 and $1,800','hr',True)]:msg(*args)
    y+=152
    band(STEPS[4],110,'selling.py: negotiate\n_fresh_terms\nsale_decisions.py\nanswer_counter\ncore/negotiation.py: respond')
    for args in [(0,1,8,'"I need $2,100."'),(1,2,22,'POST /negotiate {load_id, rate, run_id}','hr'),(2,3,36,'TMS TCP: fresh LOAD_GET','ext'),(3,2,50,'raw load detail','ext',True),(2,4,64,'price + atomic answer_counter; ask / round / offer + event','data'),(2,1,78,'counter, offer=1900, round=1','svc',True),(1,0,92,'"I can do $1,900."','hr',True)]:msg(*args)
    y+=110
    band(STEPS[5],138,'selling.py: negotiate\nsale_decisions._apply\nbookings.py: reserve\nsale_decisions.settle\nRep snapshot: posted, no cap.\nThree separate row writes.')
    for args in [(0,1,8,'"Yes, $1,900 works."'),(1,2,22,'POST /negotiate {load_id, 1900, run_id}','hr'),(2,3,36,'TMS TCP: fresh LOAD_GET again','ext'),(3,2,50,'raw load detail','ext',True),(2,4,64,'1. fresh price / ACCEPT -> calls.accepting {id, load, MC, rate}','data'),(2,4,78,'2. bookings: RESERVED + terms snapshot + event','data'),(2,4,92,'3. calls: agreement + clear claim + event','data'),(2,1,106,'agreed, load_id, rate=1900','svc',True),(1,0,120,'Mocked handoff: "A senior rep will confirm."','hr',True)]:msg(*args)
    y+=138
    band(STEPS[6],96,'selling.py: close\ncalls.py: end\nCallRows.step\nEnd: if delivered')
    for args in [(1,2,8,'POST /calls/close {run_id, summary}','hr'),(2,4,22,'first closed_at + summary + event; hold unchanged','data'),(2,1,36,'closed','svc',True),(1,0,50,'Farewell; voice session ends','hr',True),(1,2,64,'V4 /calls/ended {run_id, end data}','hr',True),(2,4,78,'ended_at / ended_by / duration + event, if delivered','data')]:msg(*args)
    p.rect(44,1126,1592,27,C['soft'],C['muted'],7,True)
    p.text(57,1145,'SEPARATE REP PATH: App -> service -> Twin review. It may run while I am on the call. Only a rep Confirm may send LOAD_BOOK. No voice booking tool; no real transfer; RESERVED is not BOOKED.',13,C['muted'])
    p.footer();return p.issues


def module(p,x,y,w,h,title,build,body):
    p.rect(x,y,w,h,C['paper'],C['svc'],8)
    split=' + ' in title and stringWidth(title,'Courier',13)>w-92
    if split:
        first,second=title.split(' + ',1);p.file(x+12,y+23,first,size=13);p.file(x+12,y+41,second,size=13)
    else:p.file(x+12,y+23,title,size=13)
    p.badge(x+w-55,y+9,build,'build')
    end=p.text(x+13,y+(70 if split else 52),body,13.1,C['svc'],width=w-26,leading=16.2)
    if end>y+h:p.issues.append(f'Module height {title}')


def nested():
    p=Page('03-nested-systems-map','Where each call moment lives','Containment map separates managed runtime, repo code, transient objects and external stored state.')
    p.common('3','Nested systems map: ownership and implementation','Match C1-C7 to the blueprint and sequence. B1-B5 badges describe construction, not time or call state.')
    cw=1592/7
    for i,s in enumerate(STEPS):
        x=44+i*cw;p.rect(x,258,cw,104,C['soft'],C['line'],7);p.badge(x+10,267,s['id']);p.text(x+51,286,s['title'],14,C['ink'],'Helvetica-Bold')
        phrases=['MC -> carrier name?','Yes -> code in inbox','[code] -> verified','Lane -> LD90001, $1,800','$2,100 -> counter $1,900','Yes $1,900 -> mocked handoff','Goodbye -> notes + end report']
        p.text(x+11,316,phrases[i],13.7,C['muted'],width=cw-22,leading=17)
    # Managed platform, explicitly outside Python code.
    p.rect(44,382,322,654,C['hrbg'],C['hr'],12)
    p.text(62,410,'HAPPYROBOT MANAGED RUNTIME',16,C['hr'],'Helvetica-Bold')
    p.rect(60,432,290,110,C['paper'],C['hr'],9)
    p.text(75,456,'Web call + media / turns',16,C['hr'],'Helvetica-Bold')
    p.text(75,480,'Speech to text, model tool choice, text to speech. No repo STT/TTS implementation; provider/settings not established here.',14,C['hr'],width=260)
    p.rect(60,548,290,224,C['paper'],C['hr'],9)
    p.text(75,573,'Six model-selected tools',16,C['hr'],'Helvetica-Bold')
    p.text(75,599,'C1 verify_carrier\nC2 send_code\nC3 verify_code\nC4 find_loads\nC5-C6 negotiate\nC7 close_call',14,C['hr'],'Courier',width=260,leading=23)
    p.text(75,759,'No LOAD_BOOK tool.',14,C['hr'],'Helvetica-Bold')
    p.rect(60,788,290,105,C['paper'],C['hr'],9)
    p.text(75,814,'Trusted runtime envelope',15,C['hr'],'Helvetica-Bold')
    p.text(75,837,'current.run_id + agent key. Model supplies only step arguments; service rejects invented state.',14,C['hr'],width=260)
    p.rect(60,909,290,111,C['paper'],C['hr'],9,True)
    p.text(75,934,'C7 post-agent end callback',15,C['hr'],'Helvetica-Bold')
    p.text(75,959,'Version 4 draft; initiator + duration. Capture only if executed and Twin accepts it. Mock transfer is speech only.',13.8,C['hr'],width=260)
    # Repo boundary nests service, app and prompt files.
    p.rect(404,382,936,654,'none',C['svc'],12,False,2)
    p.text(423,410,'REPO IMPLEMENTATION',17,C['svc'],'Helvetica-Bold')
    p.text(680,409,'Python service + App + prompt configuration copies',14,C['muted'])
    p.rect(417,424,910,445,C['svcbg'],C['svc'],10)
    p.text(432,447,'PYTHON SERVICE: receives requests; owns decisions, integrations and row writes',14.4,C['svc'],'Helvetica-Bold')
    module(p,431,460,882,72,'main.py + config.py + api.py','B2','build/load_settings wires explicit dependencies. API authenticates + validates JSON; 12-second per-tool deadline. B3/B4 extend routes.')
    module(p,431,545,277,168,'calls.py','B2','C1-C3 Calls.verify_carrier / send_code / verify_code.\nC7 Calls.end.\nCallRows.step saves one row state + its event.')
    module(p,720,545,294,168,'selling.py + sale_decisions.py','B3','C4 find_loads / _open_loads.\nC5-C6 negotiate -> answer_counter -> _apply / settle.\nC7 Sales.close.\nOrchestrate rules and effects.')
    module(p,1026,545,287,168,'core/','B1','Pure rules + typed values.\nB1 loads, pricing, money, negotiation. B2 carrier_policy + codes.\npublic_view excludes ceiling + posted rate.')
    module(p,431,726,277,127,'adapters/','B2','Twin.change: CAS row writes.\nFmcsa.carriers / CodeMailer.send [B2]. TmsClient.query/get + protocol/mapping [B1].')
    module(p,720,726,294,127,'bookings.py','B3','C6 reserve / void: booking row decides holder. Preserve freed-row history.\nClaim recovery spans rows; not a DB transaction.')
    module(p,1026,726,287,127,'rep_actions.py','B4','OUTSIDE VOICE: confirm -> fresh recheck -> SUBMITTING -> _send -> classify.\nOnly caller of TmsClient.book.')
    module(p,417,885,562,137,'ops-app/ + service/dashboard.py','B4','HomePage -> getSnapshot -> Dashboard.snapshot -> build_snapshot.\nprojectSnapshot / RepQueue show terms, asks, history, mode and next action.\nVerified rep + version -> postRepAction -> RepActions.confirm.\nApp reads/writes through service, never directly to Twin or TMS.')
    module(p,992,885,335,137,'happyrobot/prompt*.md','B5','Review copies of native prompts.\nB2 verify + B3 sales configuration.\nName Yes and spoken handoff are prompt behavior, not service flags.\nV4 draft; voice acceptance open.')
    # Transport arrows cross code/runtime boundary, not data-state boundaries.
    p.line(350,565,410,565,C['hr'],2,False,True);p.text(354,551,'JSON',12,C['hr'])
    p.line(410,590,350,590,C['svc'],2,True,True);p.text(355,610,'Reply',12,C['svc'])
    # External systems.
    p.text(1370,410,'EXTERNAL TO REPO',16,C['ext'],'Helvetica-Bold')
    exts=[(430,88,'FMCSA | C1','HTTP carrier records only.\nEligibility decided in service.'),(535,88,'Gmail SMTP | C2','Configured demo inbox.\nSMTP accepted != read.\nInbox access != identity.'),(640,110,'Legacy TMS | C4-C6','Raw TCP QUERY / GET [B1].\nFresh connection per attempt.\nPer read: 6s total; <=3 tries.\nB4 BOOK only on rep path.')]
    for yy,hh,title,body in exts:
        p.rect(1370,yy,266,hh,C['extbg'],C['ext'],12);p.text(1385,yy+27,title,15,C['ext'],'Helvetica-Bold');p.text(1385,yy+51,body,13.1,C['ext'],width=236,leading=16)
        p.line(1341,yy+hh/2,1366,yy+hh/2,C['ext'],1.5,False,True)
    p.store(1370,775,266,116,'Twin native: calls[run_id]','version + data: MC, authority, OTP hash, offers, rounds, claim/agreement, notes, events',13)
    p.store(1370,911,266,125,'Twin: bookings[load_id]','version + data: RESERVED, call_id, MC, rate, shipment snapshot and history. Posted rate for rep, no ceiling. Not TMS booking.',13)
    p.line(1341,832,1366,832,C['data'],1.5,False,True);p.line(1341,970,1366,970,C['data'],1.5,False,True)
    p.rect(44,1052,1592,42,C['databg'],C['data'],8)
    p.text(58,1078,'TRANSIENT DATA OBJECTS (not tables): Authority | CodeState | Search | LoadSummary -> Load | Terms -> Step | public load dict -> JSON Reply. Raw ceiling stays inside service.',13.8,C['data'])
    p.rect(44,1106,1592,49,C['soft'],C['muted'],8,True)
    p.text(58,1128,'IMPLEMENTED, CONDITIONAL REP PATH [B4]: sends off/unknown disables Confirm. If enabled and approved, send LOAD_BOOK once; PENDING -> ACK_PENDING, not CONFIRMED.',13.8,C['ink'])
    p.text(58,1147,'No actual transfer, automatic TMS finalization, direct App-to-Twin path, separate audit database, or repo-owned speech engine is implemented.',13,C['muted'])
    p.footer();return p.issues


def main():
    issues=blueprint()+sequence()+nested()
    writer=PdfWriter()
    for stem in ['01-caller-blueprint','02-call-sequence','03-nested-systems-map']:
        reader=PdfReader(PAGES/f'{stem}.pdf');assert len(reader.pages)==1;writer.add_page(reader.pages[0])
    writer.add_metadata({'/Title':'My successful call: three systems views','/Subject':'Implemented main 2678845, not a live-call guarantee'})
    with (OUT/'caller-journey-three-views.pdf').open('wb') as f:writer.write(f)
    (HERE/'trace.json').write_text(json.dumps({'source_commit':'2678845','call_steps':STEPS,'shape_meanings':{'C':'call moment','B':'build slice','file':'code','capsule':'transient data','cylinder':'saved state'},'render_issues':issues},indent=2)+'\n')
    template=(HERE/'viewer-template.html').read_text()
    (OUT/'index.html').write_text(template.replace('TRACE_DATA_PLACEHOLDER',(HERE/'trace.json').read_text().strip()))
    if issues:raise SystemExit('\n'.join(issues))
    print('Built three single-page SVG/PDF pairs and the three-page combined PDF.')


if __name__=='__main__':main()
