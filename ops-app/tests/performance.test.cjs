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

test('cohort comes from voice run IDs and counts historical reservations across deployment tags', () => {
  const r = report([
    reservation(a, 130, [found({ offers: { LD1: 100 } })]),
    call(b, { cohort: 'real', events: [found({ loads: [{ load_id: 'LD2', offer: 140 }] })] }),
    call(c, { events: [{ action: 'find_loads', status: 'no_match' }] }), call(d, { code_passed: false }),
    reservation('some-other-workflow-or-text-run', 450, [found({ offers: { LD1: 100 } })]),
    call('selftest-20261103-deploy', { cohort: 'real' }),
    call('aa37c921-2b86-40e9-b9b4-a060a372f9d5'), // platform-marked missed session
    call(d, { code_passed: false }), // duplicate projection
  ]);
  assert.deepEqual(Object.fromEntries(Object.entries(r.groups).map(([k, v]) => [k, v.map(x => x.id)])),
    { recorded: [a,b,c,d], verified: [a,b,c], matched: [a,b], reserved: [a], paired: [a], unmatched: [c], 'no-agreement': [b] });
  assert.equal(r.conversion, 33);
  assert.equal(r.sessionCount, 50);
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
