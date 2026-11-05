const assert = require('node:assert/strict');
const test = require('node:test');
const loadTs = require('./load-ts.cjs');
const { projectSnapshot } = loadTs('src/lib/snapshot.ts');
const { performance, usd } = loadTs('src/lib/performance.ts');
const { demoVoiceRunIds } = loadTs('src/lib/demo-voice-runs.ts');
const [a, b, c, d, e] = demoVoiceRunIds;
const found = (data) => ({ action: 'find_loads', status: 'found', ...data });
const call = (id, more = {}) => ({ id, cohort: 'synthetic', code_passed: true, ...more });
const reservation = (id, rate, events) => call(id, {
  booking: { load_id: 'LD1', state: 'RELEASED' }, agreement: { load_id: 'LD1', rate }, events,
  offers: { LD1: rate }, // latest price cannot reconstruct the opening
});
const report = (calls) => performance(projectSnapshot({ status: 'ok', calls, bookings: [] }).calls);

test('all workflow versions and deployment tags count without a fixed inventory limit', () => {
  const newer='12345678-1234-1234-1234-123456789abc';
  const missed='aa37c921-2b86-40e9-b9b4-a060a372f9d5';
  const r=report([reservation(a,130,[found({offers:{LD1:100}})]),
    call(b,{cohort:'real',events:[found({offers:{LD2:140}})]}),
    call(c,{events:[{action:'find_loads',status:'no_match'}]}),call(d,{code_passed:false}),
    reservation(newer,450,[found({offers:{LD1:400}})]),call('selftest-probe'),
    call(missed,{code_passed:false}),call(d,{code_passed:false})]);
  assert.deepEqual(r.groups.recorded.map(c=>c.id),[a,b,c,d,newer,missed]);
  assert.deepEqual(r.groups.reserved.map(c=>c.id),[a,newer]);
  assert.equal(r.groups.verified.length,4);
  assert.equal(r.conversion,50);assert.equal(r.sessionCount,6);assert.equal(r.missedCount,1);
});

test('pairs opening by call and load before the 100-event timeline limit, with both event formats', () => {
  const repeated = { loads: [{ load_id: 'LD1', offer: 120 }] };
  const r = report([
    reservation(a, 145, [found({ offers: { LD2: 500 } }), found({ offers: { LD1: 100 } }),
      ...Array(101).fill({ action: 'verify_code', status: 'verified' }), found(repeated)]),
    reservation(b, 1000, [found({ loads: [{ load_id: 'LD2', offer: 5000 }, { load_id: 'LD1', offer: 975 }] })]),
  ]);
  assert.equal(r.groups.paired.length, 2);
  assert.equal(r.medianConcession, 35);
  assert.deepEqual(r.groups.paired.map(x => x.openingRate), [100, 975]);
});

test('missing first price and inconsistent agreement identity stay out of the median, with no zero-denominator claims', () => {
  const r = report([
    reservation(a, 140, [found({ loads: [{ load_id: 'LD1' }] }), found({ offers: { LD1: 100 } })]),
    { ...reservation(b, 130, [found({ offers: { LD1: 90 } })]), agreement: { load_id: 'LD2', rate: 130 } },
    reservation(c, 200, [found({ offers: { LD2: 150 } })]),
    reservation(d, 140, [found({ offers: { LD1: 120 } })]),
    reservation(e, 130, [found({ offers: { LD1: 105 } })]),
  ]);
  assert.equal(r.groups.reserved.length, 5);
  assert.equal(r.groups.paired.length, 2);
  assert.equal(usd(r.medianConcession), '$22.5');
  const missingSearch = report([reservation(a, 200, [])]);
  assert.equal(missingSearch.groups.reserved.length, 1);
  assert.equal(missingSearch.groups.unmatched.length, 0);
  assert.equal(report([]).conversion, null);
  assert.equal(report([]).medianConcession, null);
});


test('new call duration uses the workflow end report instead of subtracting tool timestamps', () => {
  const fresh='12345678-1234-1234-1234-123456789abc';
  const r=report([call(fresh,{started_at:'2026-11-04T00:00:00Z',ended_at:'2026-11-04T00:10:00Z',duration_seconds:35})]);
  assert.equal(r.medianSeconds,35);
  assert.equal(r.durationCount,1);
  const missing=report([call(fresh,{started_at:'2026-11-04T00:00:00Z',ended_at:'2026-11-04T00:10:00Z'})]);
  assert.equal(missing.medianSeconds,null);
});

test('overview date range sorts actual dates and labels the Central calendar date', () => {
  const {dateRange}=loadTs('src/components/performance.tsx');
  assert.equal(dateRange({groups:{recorded:[{sessionAt:'2026-01-01T02:00:00Z'},{sessionAt:'2025-11-03T14:00:00Z'}]}}),
    'Nov 3, 2025 to Dec 31, 2025 (CT)');
});


test('active verified calls are not losses, and ended records move into the appropriate loss groups', () => {
  const freshA='12345678-1234-1234-1234-123456789abc';
  const freshB='12345678-1234-1234-1234-123456789abd';
  const rows=[call(freshA),call(freshB,{events:[found({offers:{LD1:100}})]})];
  const active=report(rows);
  assert.equal(active.groups.unmatched.length,0);
  assert.equal(active.groups['no-agreement'].length,0);
  assert.equal(active.groups.unresolved.length,2);
  assert.equal(active.completedCount,0);
  assert.equal(active.groups.verified.length,2);
  const ended=report(rows.map(c=>({...c,ended_at:'2026-11-05T10:00:00Z'})));
  assert.equal(ended.groups.unmatched.length,1);
  assert.equal(ended.groups['no-agreement'].length,1);
  assert.equal(ended.groups.unresolved.length,0);
  assert.equal(ended.completedCount,2);
});
