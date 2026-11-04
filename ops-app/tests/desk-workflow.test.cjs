const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const load = require('./load-ts.cjs');
const { projectSnapshot } = load('src/lib/snapshot.ts');
const { platformRun, workspaceFilters } = load('src/lib/views.ts');
const { demoVoiceRunIds } = load('src/lib/demo-voice-runs.ts');
const [old, current] = demoVoiceRunIds;
const link = ({ href, children }) => React.createElement('a', { href }, children);
const shell = ({ actions, children }) => React.createElement('main', null, actions, children);
const base = { 'next/link': { __esModule: true, default: link },
  'next/navigation': { useRouter: () => ({ refresh() {} }) }, '@/components/app-shell': { AppShell: shell },
  '@/components/auto-refresh': { AutoRefresh: () => null }, '@/components/receipt-panels': { ReceiptPanels: () => null },
  '@/lib/auth': { requireAppUser: async () => ({ user: {} }) } };
const evt = (action, status, extra = {}) => ({ action, status, ...extra });
const reserve = (id, rate, state, cohort) => ({ id, cohort, mc: '123456', carrier_name: 'Fixture Freight', code_passed: true, rounds: 1,
  events: [evt('find_loads', 'found', { offers: { LD1: rate-25 } }), evt('negotiate','agreed')],
  booking: { load_id: 'LD1', state }, agreement: { load_id: 'LD1', rate } });
const source = { status:'ok', live_booking: false, generated_at:'2026-11-04T12:35:00Z',
  calls: [reserve(old,500,'RELEASED','real'), reserve(current,1000,'RESERVED','synthetic'),
    { id:'selftest-20261103-deploy', cohort:'real', carrier_name:'Probe' }],
  bookings: [{ load_id:'LD1', call_id:current, cohort:'synthetic', version:2, state:'RESERVED', mc:'123456',
    carrier_name:'Fixture Freight', rate:1000, load:{origin:{city:'Dallas',state:'TX'},destination:{city:'Atlanta',state:'GA'}} }] };
async function page(data, params) {
  const ops = load('src/lib/ops-service.ts');
  const { default: Home } = load('src/app/page.tsx', { ...base, '@/lib/ops-service': {
    ...ops, getSnapshot: async () => ({ok:true,snapshot:projectSnapshot(data)}) } });
  return renderToStaticMarkup(await Home({searchParams:Promise.resolve(params)}));
}
test('home lists the current owner and a history link; its direct review shows matching rates, native recording and send guard', async () => {
  const home = await page(source,{});
  assert.match(home,/Awaiting rep \(1\)/); assert.match(home,/Reservation history \(2\)/);
  assert.ok(home.includes('Opened $975')); assert.ok(home.includes('Review reservation'));
  assert.ok(!home.includes('Activity scope'));
  const hp = await page(source,{view:'reservations',load:'LD1',run:current});
  for (const s of ['Fixture Freight','$975','$1,000','Originating call timeline',platformRun(current),'View only']) assert.ok(hp.includes(s),s);
});
test('a superseded agreement on a reused load opens only the originating history and has no mutating controls', async () => {
  const hp = await page(source,{view:'reservations',load:'LD1',run:old});
  for(const s of ['$475','$500','Historical agreement',platformRun(old)]) assert.ok(hp.includes(s),s);
  assert.ok(!hp.includes('>Confirm</button>')); assert.ok(!hp.includes('$1,000'));
  const wrong = await page(source,{view:'bookings',load:'LD1',run:'wrong'});
  assert.ok(wrong.includes('unavailable')); assert.ok(!wrong.includes('>Confirm</button>'));
});
test('email retries, earlier eligibility and legacy repeated counter rounds count once per call', () => {
  const { callMilestones }=load('src/lib/call-milestones.ts');
  const m=callMilestones([evt('verify_carrier','eligible'),evt('verify_carrier','not_found'),evt('send_code','code_issued'),
    evt('send_code','send_failed'),evt('negotiate','counter',{round:1}),evt('negotiate','counter',{round:1}),
    evt('negotiate','counter',{round:2}),evt('negotiate','final_offer',{round:3}),evt('negotiate','negotiation_failed')]);
  assert.equal(m.authorityPassed,true); assert.equal(m.codeIssued,true); assert.equal(m.counters,3); assert.equal(m.finalLimit,true);
  assert.equal(callMilestones([evt('negotiate','accepting'),evt('negotiate','agreed')]).counters,0);
  assert.equal(callMilestones([evt('negotiate','counter')]).counters,null);
  assert.equal(callMilestones([evt('negotiate','final_offer',{round:3})]).finalLimit,false);
});
test('filters respect Central day boundaries, offered load IDs and match scope of the requested result', () => {
  const { filterCalls, filterBookings }=load('src/components/record-search.tsx',base);
  const c={id:current,sessionAt:'2026-11-04T01:05:00Z',mc:'123456',search:'REEFER / TX / GA',offeredIds:['LD100'],outcome:'no_match'};
  const b={callId:current,loadId:'LD100',state:'RESERVED',load:{origin:'Dallas, TX'}};
  const f=(over)=>workspaceFilters({from:'2026-11-03',to:'2026-11-03',...over});
  assert.equal(filterCalls([c],f({q:'ld100',status:'no_match'})).length,1);
  assert.equal(filterCalls([c],f({q:'reefer',from:'2026-11-04'})).length,0);
  assert.equal(filterBookings([b],f({q:'dallas',status:'RESERVED'}),new Map([[current,c]])).length,1);
  assert.equal(platformRun('invalid'),null);
});
test('new service UUIDs appear in the operational log, outside the dated voice funnel', async () => {
  const future='12345678-1234-1234-1234-123456789abc';
  const data={...source,calls:[...source.calls,{id:future,carrier_name:'Future carrier',cohort:'synthetic'}]};
  assert.ok((await page(data,{view:'calls'})).includes('Future carrier'));
  assert.ok(!(await page(data,{view:'calls'})).includes('Probe'));
  assert.ok(!(await page(data,{group:'recorded'})).includes('Future carrier'));
});

test('booking evidence separates preflight, explicit TMS rejection and ambiguous transport', () => {
  const { submissionStatus } = load('src/lib/format.ts');
  for (const reason of ['not_sent','load_gone','ceiling_below_rate','load_not_open']) assert.equal(submissionStatus('FAILED',reason,null),'Not submitted');
  for (const reason of ['unknown_load','not_found','invalid_rate']) assert.equal(submissionStatus('FAILED',reason,null),'Rejected by TMS');
  assert.equal(submissionStatus('UNKNOWN','no_complete_reply',null),'Outcome unknown');
  assert.equal(submissionStatus('FAILED',null,null),'Submission evidence unavailable');
  assert.equal(submissionStatus('ACK_PENDING',null,'PENDING'),'Acknowledged, pending');
});

test('demand follows the empty search evidence when a later request changes lane', () => {
  const {callMilestones}=load('src/lib/call-milestones.ts');
  const a={origin_state:'ME',dest_state:'GA'}, b={origin_state:'TX',dest_state:'TN'};
  const empty=evt('find_loads','no_match'), outage=evt('find_loads','tms_unavailable',{search:b});
  assert.equal(callMilestones([{...empty,search:a},outage],b).noMatchLane,'any / ME / GA');
  assert.equal(callMilestones([empty,outage],b).noMatchLane,null);
  assert.equal(callMilestones([empty],a).noMatchLane,'any / ME / GA');
});
