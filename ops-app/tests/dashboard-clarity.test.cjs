const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const loadTs = require('./load-ts.cjs');

const link = ({ href, children }) => React.createElement('a', { href }, children);
const nav = { useRouter: () => ({ refresh() {} }) };
const overrides = { 'next/link': { __esModule: true, default: link }, 'next/navigation': nav };
const { CallResults } = loadTs('src/components/call-results.tsx', overrides);
const { CurrentWork } = loadTs('src/components/current-work.tsx', overrides);
const { EventList } = loadTs('src/components/ops-events.tsx', overrides);
const { events } = loadTs('src/lib/event-history.ts');
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
const kpis = { calls: 4, codePassed: 3, handoffs: 1, northstar: .333, repConfirmed: 1,
  tmsAcknowledged: 1, tmsConfirmed: 0, unknown: 0, medianSecondsToFirstOffer: 27,
  closedWithSummary: 2, endsReported: 0, syntheticCalls: 41 };

test('conversion explains denominator, time range and sample without hovering', () => {
  const html = render(CallResults, { calls: [], kpis });
  for (const text of ['33%', '1 of 3 email-verified calls', 'all recorded history', 'Small demo sample',
    'Calls recorded', 'Email code verified', 'Reservations created', 'including later failed submissions']) {
    assert.ok(html.includes(text), text);
  }
  assert.ok(!html.includes('Northstar'));
  assert.ok(!html.includes('Tool-to-offer'));
});

test('zero and missing denominators never show a misleading percentage', () => {
  const zero = render(CallResults, { calls: [], kpis: { ...kpis, codePassed: 0, handoffs: 0, northstar: null } });
  assert.match(zero, /No rate yet/);
  assert.match(zero, /No email-verified calls recorded yet/);
  assert.ok(!zero.includes('NaN'));
  const missing = render(CallResults, { calls: [], kpis: { ...kpis, codePassed: null, handoffs: null, northstar: null } });
  assert.ok(missing.includes('Not recorded'));
});

test('test results contain only test call history and no business conversion', () => {
  const html = render(CallResults, { calls: [{ codePassed: true, bookingLoadId: 'released-history' },
    { codePassed: true, bookingLoadId: null }], kpis: null });
  assert.match(html, /Test call results/);
  assert.match(html, /Excluded from business performance/);
  assert.ok(!html.includes('Reservation conversion'));
  assert.ok(!html.includes('33%'));
});

test('current booking work is separate from historical approvals and released reservations', () => {
  const html = render(CurrentWork, { scope: 'test', bookings: [
    { state: 'RESERVED' }, { state: 'RELEASED' }, { state: 'UNKNOWN' },
    { state: 'ACK_PENDING' }, { state: 'CONFIRMED' }, { state: 'FAILED' },
  ] });
  for (const text of ['Awaiting rep review', 'Submission outcome unknown', 'Awaiting TMS confirmation',
    'TMS-confirmed bookings', 'PENDING, not final', '/?view=reservations&amp;scope=test']) {
    assert.ok(html.includes(text), text);
  }
  assert.ok(!html.includes('Rep approved'));
  assert.equal((html.match(/tabular-nums">1</g) ?? []).length, 4);
});

test('timeline keeps asks, round, price and technical reference in expandable details', () => {
  const html = render(EventList, { events: events([{ action: 'negotiate', status: 'counter',
    heard: '3000', ask: 3000, offer: 2825, round: 1, call_id: 'record-ref', max_rate: 987654 }]) });
  for (const text of ['Amount checked: $3,000', 'Our offer: $2,825', 'Counter round: 1',
    '<details', 'Technical details', 'Call reference: record-ref']) assert.ok(html.includes(text), text);
  assert.ok(!html.includes('987654'));
});

test('reservation panel puts the decision and agreed payment before shipment detail', () => {
  const detail = loadTs('src/components/detail-sheet.tsx');
  const { RepQueue } = loadTs('src/components/rep-queue.tsx', { ...overrides,
    '@/components/detail-sheet': { ...detail, DetailSheet: ({ children }) => React.createElement('div', null, children) },
  });
  const html = render(RepQueue, { title: 'Queue', description: 'Fixture', now: 0, liveBooking: false,
    rows: [{ loadId: 'LD1', version: 1, state: 'RESERVED', carrierName: 'Fixture Carrier', rate: 2750, events: [] }] });
  assert.ok(html.indexOf('Next action') < html.indexOf('>Load</h3>'));
  assert.match(html, /\$2,750.*agreed carrier payment/);
  assert.match(html, /Not submitted/);
});

test('unknown send mode disables Confirm without disabling Decline', () => {
  const { RepQueue } = loadTs('src/components/rep-queue.tsx', overrides);
  const html = render(RepQueue, { title: 'Queue', description: 'Fixture', now: 0, liveBooking: null,
    rows: [{ loadId: 'LD1', version: 1, state: 'RESERVED', events: [] }] });
  assert.match(html, /Send mode unknown/);
  assert.match(html, /disabled=""[^>]*>Confirm/);
  const decline = html.match(/<button([^>]*)>Decline<\/button>/);
  assert.ok(decline);
  assert.doesNotMatch(decline[1], /\sdisabled(?:=|\s|$)/);
});

test('Test overview does not receive real-only KPIs and keeps current work ahead of results', async () => {
  const realOps = loadTs('src/lib/ops-service.ts');
  const stub = ({ children }) => React.createElement('div', null, children);
  const snapshot = { liveBooking: false, generatedAt: '2026-11-04T10:00:00Z', kpis,
    calls: [{ id: 'fixture-test', cohort: 'synthetic', codePassed: true, bookingLoadId: 'LD1', events: [] }],
    bookings: [], turnedAway: [] };
  const { default: HomePage } = loadTs('src/app/page.tsx', {
    ...overrides, '@/lib/auth': { requireAppUser: async () => ({ user: {} }) },
    '@/lib/ops-service': { ...realOps, getSnapshot: async () => ({ ok: true, snapshot }) },
    '@/components/app-shell': { AppShell: stub }, '@/components/auto-refresh': { AutoRefresh: stub },
    '@/components/receipt-panels': { ReceiptPanels: stub },
  });
  const html = renderToStaticMarkup(await HomePage({ searchParams: Promise.resolve({ scope: 'test' }) }));
  assert.ok(html.includes('Test call results'));
  assert.ok(!html.includes('33%'));
  assert.ok(!html.includes('Historically approved for submission'));
  assert.ok(html.indexOf('Awaiting rep review') < html.indexOf('Test call results'));
});
