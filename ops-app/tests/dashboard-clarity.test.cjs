const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const loadTs = require('./load-ts.cjs');

const link = ({ href, children }) => React.createElement('a', { href }, children);
const nav = { useRouter: () => ({ refresh() {} }) };
const overrides = { 'next/link': { __esModule: true, default: link }, 'next/navigation': nav };
const { EventList } = loadTs('src/components/ops-events.tsx', overrides);
const { events } = loadTs('src/lib/event-history.ts');
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
test('timeline keeps asks, round, price and technical reference in expandable details', () => {
  const html = render(EventList, { events: events([{ action: 'negotiate', status: 'counter',
    heard: '3000', ask: 3000, offer: 2825, round: 1, call_id: 'record-ref', max_rate: 987654 }]) });
  for (const text of ['Amount checked: $3,000', 'Our offer: $2,825', 'Pricing round: 1',
    '<details', 'Technical details', 'Call reference: record-ref']) assert.ok(html.includes(text), text);
  assert.ok(!html.includes('987654'));
});

const { ReservationReview } = loadTs('src/components/reservation-review.tsx', overrides);
const booking = { loadId: 'LD1', version: 1, state: 'RESERVED', carrierName: 'Fixture Carrier', rate: 2750, events: [] };

test('review shows the agreement and next action before the full record', () => {
  const html = render(ReservationReview, { booking, canManage: true, live: false, now: 0 });
  assert.ok(html.indexOf('Agreed rate') < html.indexOf('Booking and shipment'));
  for (const text of ['$2,750', 'Not submitted', 'Originating call timeline', 'Confirm is disabled']) assert.ok(html.includes(text), text);
});

test('unknown send mode disables Confirm without disabling Decline in review', () => {
  const html = render(ReservationReview, { booking, canManage: true, live: null, now: 0 });
  assert.match(html, /Send mode unavailable/);
  assert.match(html, /disabled=""[^>]*>Confirm/);
  assert.doesNotMatch(html.match(/<button([^>]*)>Decline<\/button>/)[1], /\sdisabled(?:=|\s|$)/);
});
