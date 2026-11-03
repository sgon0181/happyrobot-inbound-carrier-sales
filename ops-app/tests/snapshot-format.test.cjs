const assert = require('node:assert/strict');
const test = require('node:test');
const loadTs = require('./load-ts.cjs');
const { projectSnapshot } = loadTs('src/lib/snapshot.ts');
const { fmtTime, label, nextAction } = loadTs('src/lib/format.ts');

test('rep snapshot includes allowed terms, excludes private fields, and leaves legacy rows missing', () => {
  const result = projectSnapshot({ status: 'ok', bookings: [
    { load_id: 'LD09001', version: 1, carrier_name: 'Carrier A', load: {
      origin: { city: 'Dallas', state: 'TX' }, destination: { city: 'Atlanta', state: 'GA' },
      pickup_datetime: '2026-11-03T12:00:00Z', loadboard_rate: 2150, max_rate: 9876543, secret: 'private-token' } },
    { load_id: 'OLD', version: 3 },
  ], calls: [] });
  assert.equal(result.bookings[0].load.origin, 'Dallas, TX');
  assert.equal(result.bookings[0].load.postedRate, 2150);
  assert.equal(result.bookings[0].carrierName, 'Carrier A');
  assert.equal(result.bookings[1].load, null);
  assert.ok(!JSON.stringify(result).includes('9876543'));
  assert.ok(!JSON.stringify(result).includes('private-token'));
});

test('Central Time uses winter and summer offsets, and never invents missing dates', () => {
  assert.equal(fmtTime('2026-01-15T12:00:00Z'), '2026-01-15 06:00 CT');
  assert.equal(fmtTime('2026-07-15T12:00:00Z'), '2026-07-15 07:00 CT');
  assert.equal(fmtTime(null), 'Not recorded');
  assert.equal(fmtTime('invalid'), 'Not recorded');
});

test('operational labels preserve pending, final, and unknown distinctions', () => {
  assert.equal(label('ACK_PENDING'), 'Sent, TMS pending');
  assert.equal(label('CONFIRMED'), 'TMS confirmed');
  assert.equal(label(null), 'Not recorded');
  assert.match(nextAction('UNKNOWN'), /Never resend/);
  assert.match(label('future_status'), /Future status/);
});

test('unknown or malformed send mode stays unknown rather than enabling Confirm', () => {
  const base = { status: 'ok', calls: [], bookings: [] };
  assert.equal(projectSnapshot(base).liveBooking, null);
  assert.equal(projectSnapshot({ ...base, live_booking: 'true' }).liveBooking, null);
  assert.equal(projectSnapshot({ ...base, live_booking: false }).liveBooking, false);
  assert.equal(projectSnapshot({ ...base, live_booking: true }).liveBooking, true);
});
