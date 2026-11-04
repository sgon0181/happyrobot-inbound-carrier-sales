const assert = require('node:assert/strict');
const test = require('node:test');
const loadTs = require('./load-ts.cjs');
const { events } = loadTs('src/lib/event-history.ts');

test('projects actual public_view strings, pitch details and search criteria', () => {
  const [event] = events([{
    seq: 1, action: 'find_loads', status: 'found',
    search: { equipment: 'DRY_VAN', origin_state: 'TX', dest_state: 'GA' },
    loads: [{ load_id: 'LD09001', origin: 'Dallas, TX', destination: 'Atlanta, GA',
      offer: 1900, pickup_datetime: '2099-12-31T08:00:00+00:00', weight: 42000,
      notes: 'Appointment required', max_rate: 9876543 }],
  }]);
  for (const value of ['Dallas, TX', 'Atlanta, GA', '$1,900', '42,000', 'Appointment required', 'Dry van, TX to GA', 'Dec 31, 02:00 CT']) {
    assert.ok(event.detail.includes(value), value);
  }
  assert.ok(!JSON.stringify(event).includes('9876543'));
  assert.ok(!JSON.stringify(event).includes('max_rate'));
});

test('keeps earlier asks, normalized amounts and terminal outcome without private fields', () => {
  const history = events([
    { heard: '5,000', ask: 5000, status: 'counter', offer: 2000, round: 1 },
    { heard: '5100', ask: 5100, status: 'counter', offer: 2075, round: 2 },
    { action: 'call_ended', status: 'ended', ended_by: 'user', duration_seconds: 52,
      otp: 'private-code', secret: 'private-token' },
  ]);
  assert.match(history[0].detail, /Carrier said: 5,000. Amount checked: \$5,000/);
  assert.match(history[1].detail, /Amount checked: \$5,100/);
  assert.match(history[2].detail, /Call ended by: user. Duration in seconds: 52/);
  assert.ok(!JSON.stringify(history).includes('private-'));
});

test('pitched shipment notes are redacted and use business labels rather than raw fields', () => {
  const [event] = events([{ loads: [{ load_id: 'LD1', notes: 'Verification code 123456. Maximum rate $98765',
    pickup_datetime: '2026-11-16T18:56:00Z', equipment_type: 'REEFER', num_of_pieces: 27,
    max_rate: 87654, secret: 'private-token' }], call_id: 'call-reference' }]);
  assert.match(event.detail, /Pickup: Nov 16, 12:56 CT/);
  assert.match(event.detail, /Equipment: Refrigerated/);
  assert.match(event.detail, /Pieces: 27/);
  for (const value of ['123456', '98765', '87654', 'private-token', 'pickup_datetime', 'num_of_pieces']) {
    assert.ok(!JSON.stringify(event).includes(value), value);
  }
  assert.equal(event.callId, 'call-reference');
});

test('keeps each reservation snapshot after the same booking row is freed and reused', () => {
  const snapshot = (posted, pickup, note) => ({origin:{city:'Dallas',state:'TX'}, destination:{city:'Atlanta',state:'GA'}, loadboard_rate:posted, pickup_datetime:pickup, notes:note, num_of_pieces:14, max_rate:9876543, token:'private-token'});
  const history=events([
    {action:'reserved',call_id:'first',state:'RESERVED',load:snapshot(2150,'2026-11-03T12:00:00Z','First terms')},
    {action:'declined',state:'FREED'},
    {action:'reserved',call_id:'second',state:'RESERVED',load:snapshot(2300,'2026-11-05T12:00:00Z','New terms')},
  ]);
  assert.equal(history[0].load.postedRate,2150);
  assert.equal(history[0].load.notes,'First terms');
  assert.equal(history[0].load.pieces,14);
  assert.equal(history[1].load,null);
  assert.equal(history[2].load.postedRate,2300);
  assert.notEqual(history[0].load.pickup,history[2].load.pickup);
  assert.ok(!JSON.stringify(history).includes('9876543'));
  assert.ok(!JSON.stringify(history).includes('private-token'));
});
