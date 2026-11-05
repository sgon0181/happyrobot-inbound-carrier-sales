const assert = require('node:assert/strict');
const test = require('node:test');
const load = require('./load-ts.cjs');
const { reservationCounts } = load('src/components/current-desk.tsx');
const { canManageBookings } = load('src/lib/rep-access.ts');
const route = 'src/app/api/bookings/[loadId]/[action]/route.ts';

test('reservation status includes every deployment tag without promoting pending receipts', () => {
  const rows = [{state:'RESERVED',cohort:'synthetic'}, {state:'RESERVED',cohort:'real'},
    {state:'ACK_PENDING',cohort:'synthetic'}, {state:'RELEASED',cohort:null}];
  assert.deepEqual(reservationCounts(rows), {RESERVED:2,ACK_PENDING:1,CONFIRMED:0,RELEASED:1});
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


test('fresh native recording links require immutable trusted integration provenance', () => {
  const {projectSnapshot} = load('src/lib/snapshot.ts');
  const id='12345678-1234-1234-1234-123456789abc';
  const project=native_workflow=>projectSnapshot({status:'ok',calls:[{id,native_workflow}],bookings:[]}).calls[0];
  assert.equal(project(undefined).recordingUrl,null);
  assert.equal(project({workspace:'https://attacker.example',workflow_id:'valid'}).recordingUrl,null);
  assert.equal(project({workspace:'our-workspace',workflow_id:'6oaskq84xpfc'}).recordingUrl,
    `https://platform.happyrobot.ai/our-workspace/workflows/6oaskq84xpfc/runs?run_id=${id}`);
});


test('local dev hydration origin is narrow and absent from production configuration', () => {
  const saved=process.env.NODE_ENV;
  try {
    process.env.NODE_ENV='development';
    assert.deepEqual(load('next.config.ts').default.allowedDevOrigins,['127.0.0.1']);
    process.env.NODE_ENV='production';
    assert.equal(load('next.config.ts').default.allowedDevOrigins,undefined);
    const {allowedWriteOrigin}=load('src/lib/request.ts');
    assert.equal(allowedWriteOrigin('http://127.0.0.1','https://proposal.happyrobot.dev',''),false);
  } finally { if(saved===undefined)delete process.env.NODE_ENV;else process.env.NODE_ENV=saved; }
});


test('native id-shaped platform identity authorizes the assigned rep and rejects malformed identity', async () => {
  const identity='12345678-1234-1234-1234-123456789abc';
  const posted=[];
  let body={id:identity,email:'reviewer@example.invalid'};
  const savedFetch=global.fetch;
  const overrides={
    'next/headers': {cookies:async()=>({get:name=>name==='hr_token'?{value:'fixture-token'}:undefined})},
    'next/navigation': {redirect:()=>{throw new Error('Unexpected redirect');}},
    '@/lib/auth-cookies': {APP_TOKEN_COOKIE_NAME:'hr_token',APP_REFRESH_COOKIE_NAME:'hr_refresh',
      matchesAppTwinEnvironment:token=>token==='fixture-token'},
    '@/lib/env': {getServerEnv:()=>({platformUrl:'https://identity.example.invalid'}),getPublicEnv:()=>({appSlug:'review-fixture'})},
    '@/lib/rep-access': {canManageBookings:sub=>canManageBookings(sub,identity)},
    '@/lib/ops-service': {LOAD_ID_RE:/^LD[0-9]+$/,postRepAction:async(...args)=>{posted.push(args);return{ok:true,reply:{status:'sent'}};}},
  };
  global.fetch=async(url,init)=>{
    assert.equal(url,'https://identity.example.invalid/api/apps/me');
    assert.equal(init.headers.Authorization,'Bearer fixture-token');
    return Response.json(body);
  };
  try {
    const {POST}=load(route,overrides);
    const request=()=>new Request('http://localhost/api/bookings/LD1/confirm',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({version:1,rep:'spoofed'})});
    const params={params:Promise.resolve({loadId:'LD1',action:'confirm'})};
    assert.equal((await POST(request(),params)).status,200);
    assert.deepEqual(posted,[['LD1','confirm',1,identity]]);
    for(const invalid of [{email:'reviewer@example.invalid'},{id:identity,sub:'different'},
      {id:42,sub:identity},{id:' rep '},{id:''},{id:['rep']}]) {
      body=invalid;
      assert.equal((await POST(request(),params)).status,401);
    }
    assert.equal(posted.length,1);
    const {parseAppUser}=load('src/lib/auth.ts',overrides);
    assert.equal(parseAppUser({sub:identity}).sub,identity);
    assert.equal(parseAppUser({id:identity,sub:identity}).sub,identity);
  } finally {global.fetch=savedFetch;}
});
