const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const loadTs = require('./load-ts.cjs');
const { projectSnapshot } = loadTs('src/lib/snapshot.ts');
const { RepQueue } = loadTs('src/components/rep-queue.tsx', {
  'next/navigation': { useRouter: () => ({ refresh() {} }) },
});

function render(bookings) {
  const snapshot = projectSnapshot({ status: 'ok', calls: [], bookings });
  return renderToStaticMarkup(React.createElement(RepQueue, {
    title: 'Review reservations', description: 'Fixture', rows: snapshot.bookings, now: 0, liveBooking: false,
  }));
}
test('rep can read the carrier, route, timing and both prices without raw platform logs', () => {
  const html = render([{ load_id: 'LD09001', version: 1, state: 'RESERVED', mc: '138328', carrier_name: 'Fixture Carrier', rate: 1900,
    load: { origin: { city: 'Dallas', state: 'TX' }, destination: { city: 'Atlanta', state: 'GA' },
      pickup_datetime: '2026-11-03T12:00:00Z', delivery_datetime: '2026-11-04T12:00:00Z',
      equipment_type: 'DRY_VAN', loadboard_rate: 2150 } }]);
  for (const value of ['Fixture Carrier', '138328', 'Dallas, TX', 'Atlanta, GA', '06:00 CT', 'Dry van', '$1,900', '$2,150', 'Awaiting rep']) {
    assert.ok(html.includes(value), value);
  }
  assert.ok(!html.includes('CODEX LAB'));
});
test('historical reservation details are explicitly not recorded', () => {
  const html = render([{ load_id: 'OLD', version: 1, state: 'RESERVED' }]);
  assert.ok(html.includes('Not recorded'));
  assert.ok(!html.includes('Dallas'));
});
