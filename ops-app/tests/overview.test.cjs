const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const loadTs = require('./load-ts.cjs');

const link = ({ href, children }) => React.createElement('a', { href }, children);
const { attention } = loadTs('src/components/overview.tsx', { 'next/link': { __esModule: true, default: link } });
const { readView, viewHref } = loadTs('src/lib/views.ts');
const { fmtShort } = loadTs('src/lib/format.ts');
const { lanesFrom } = loadTs('src/components/turned-away.tsx');

const now = Date.parse('2026-11-03T12:30:00Z');
const booking = (loadId, state, updatedAt) => ({ loadId, state, updatedAt, carrierName: 'Carrier', rate: 1900, load: null, events: [] });

test('needs attention puts unknown and stuck sends before reservations, and counts missing notes', () => {
  const items = attention(
    [booking('LD1', 'RESERVED', '2026-11-03T12:00:00Z'), booking('LD2', 'UNKNOWN', null),
      booking('LD3', 'SUBMITTING', '2026-11-03T12:00:00Z'), booking('LD4', 'SUBMITTING', '2026-11-03T12:29:50Z'),
      booking('LD5', 'RELEASED', null)],
    [{ outcome: 'ended_without_close' }, { outcome: 'no_match' }], now, 'real');
  assert.deepEqual(items.map((i) => i.code), ['UNKNOWN', 'SUBMITTING', 'RESERVED', 'ended_without_close']);
  assert.match(items[2].detail, /Waiting 30 min/);
  assert.match(items[3].title, /^1 call without/);
  assert.equal(items[0].href, '/?view=bookings&load=LD2');
});

test('landing and legacy links resolve to unified workspaces and group drilldowns', () => {
  assert.equal(readView({}), 'reservations');
  assert.equal(readView({ view: 'calls', scope: 'test' }), 'calls');
  assert.equal(readView({ group: 'paired' }), 'overview');
  assert.equal(viewHref('overview'), '/?view=overview');
  assert.equal(viewHref('reservations'), '/');
});

test('short table times stay in Central Time and never invent a date', () => {
  assert.equal(fmtShort('2026-01-15T12:00:00Z'), 'Jan 15, 06:00 CT');
  assert.equal(fmtShort(null), 'Not recorded');
  assert.equal(fmtShort('invalid'), 'Not recorded');
});

test('demand counts each verified no-match once even with a later generic closing outcome', () => {
  const lanes = lanesFrom([
    { codePassed: true, noMatchSeen: true, outcome: 'ended_without_agreement', noMatchLane: 'DRY_VAN / ME / GA' }, { codePassed: true, noMatchSeen: true, outcome: 'ended_without_agreement', noMatchLane: 'DRY_VAN / ME / GA' },
    { outcome: 'agreed_pending_rep', search: 'FLATBED / FL / NY' }, { outcome: 'no_match', search: null },
  ]);
  assert.deepEqual(lanes, [{ equipment: 'DRY_VAN', originState: 'ME', destState: 'GA', calls: 2 }]);
});
