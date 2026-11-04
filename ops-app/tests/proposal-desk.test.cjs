const assert = require('node:assert/strict');
const test = require('node:test');
const load = require('./load-ts.cjs');
const { deskWindow } = load('src/components/current-desk.tsx');
const { canManageBookings } = load('src/lib/rep-access.ts');
const route = 'src/app/api/bookings/[loadId]/[action]/route.ts';

test('the operator window uses real cohort, a bounded seven-day window and known times', () => {
  const today = Date.parse('2026-11-14T10:00:00Z');
  const ids = [
    ['new','real','2026-11-14T09:00:00Z'], ['future','real','2026-12-02T09:00:00Z'],
    ['test','synthetic','2026-11-14T09:00:00Z'], ['old','real','2026-11-07T10:00:00Z'],
    ['missing','real',null],
  ].map(([id,cohort,sessionAt]) => ({id,cohort,sessionAt}));
  assert.deepEqual(deskWindow(ids, today).map(c => c.id), ['new']);
});

test('mutation authorization only accepts exact assigned platform subjects', async () => {
  assert.equal(canManageBookings('viewer', ''), false);
  assert.equal(canManageBookings(undefined, 'rep-1'), false);
  assert.equal(canManageBookings('rep', 'rep-1, rep-2'), false);
  assert.equal(canManageBookings('rep-2', 'rep-1, rep-2'), true);
  for (const [user,expected] of [[null,401],[{sub:'viewer',role:'admin'},403],[{sub:'rep-1'},200]]) {
    const calls=[];
    const {POST} = load(route, {
      '@/lib/auth': {getVerifiedApiUser: async () => user},
      '@/lib/rep-access': {canManageBookings: sub => canManageBookings(sub,'rep-1')},
      '@/lib/ops-service': {LOAD_ID_RE: /^LD[0-9]+$/, postRepAction: async (...args) => {
        calls.push(args); return {ok:true,reply:{status:'sent',state:'ACK_PENDING'}};
      }},
    });
    const req = new Request('http://localhost/api/bookings/LD1/confirm', {method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({version:5,rep:'spoofed'})});
    assert.equal((await POST(req,{params:Promise.resolve({loadId:'LD1',action:'confirm'})})).status,expected);
    assert.deepEqual(calls, expected === 200 ? [['LD1','confirm',5,'rep-1']] : []);
  }
});

test('credential callbacks ignore forwarding headers and unsafe writes require an exact origin', () => {
  const {getExternalOrigin,allowedWriteOrigin}=load('src/lib/request.ts');
  const saved=process.env.OPS_APP_ORIGIN;
  try {
    process.env.OPS_APP_ORIGIN='https://broker.happyrobot.dev';
    const req={nextUrl:new URL('https://malicious.example/login'),
      headers:new Headers({'x-forwarded-host':'malicious.example','x-forwarded-proto':'http'})};
    const app=getExternalOrigin(req);
    assert.equal(app,'https://broker.happyrobot.dev');
    assert.equal(allowedWriteOrigin('https://malicious.example',app,''),false);
    assert.equal(allowedWriteOrigin(null,app,''),false);
    assert.equal(allowedWriteOrigin('null',app,''),false);
    assert.equal(allowedWriteOrigin(app,app,''),true);
    assert.equal(allowedWriteOrigin('https://platform.happyrobot.ai',app,'https://platform.happyrobot.ai'),true);
  } finally {
    if(saved===undefined)delete process.env.OPS_APP_ORIGIN;else process.env.OPS_APP_ORIGIN=saved;
  }
});
