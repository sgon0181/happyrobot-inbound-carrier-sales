const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const Renderer = require('react-test-renderer');
const loadTs = require('./load-ts.cjs');
const { act } = Renderer;
global.IS_REACT_ACT_ENVIRONMENT = true;

const stub = ({ children }) => React.createElement('div', null, children);
const button = ({ children, ...props }) => React.createElement('button', props, children);
const ui = new Proxy({}, { get: () => stub });
const icons = new Proxy({}, { get: () => stub });

test('late receipt survives queue movement, refresh, remount and snapshot outage', async () => {
  const backing = new Map();
  const timers = new Map();
  let id = 0, refreshes = 0, snapshot, resolveFetch;
  const router = { refresh() { refreshes++; } };
  global.window = {
    localStorage: { get length() { return backing.size; }, key: (i) => [...backing.keys()][i],
      getItem: (k) => backing.get(k) ?? null, setItem: (k, v) => backing.set(k, v), removeItem: (k) => backing.delete(k) },
    confirm: () => true,
    setInterval: (fn) => { timers.set(++id, fn); return id; }, clearInterval: (key) => timers.delete(key),
  };
  global.document = { visibilityState: 'visible' };
  global.fetch = () => new Promise((resolve) => { resolveFetch = resolve; });
  const realOps = loadTs('src/lib/ops-service.ts');
  const overrides = {
    'next/navigation': { useRouter: () => router },
    sonner: { toast: { success() {}, error() {} } },
    '@/lib/auth': { requireAppUser: async () => ({ user: {} }) },
    '@/lib/ops-service': { ...realOps, getSnapshot: async () => snapshot },
    '@/components/app-shell': { AppShell: stub }, '@tabler/icons-react': icons,
  };
  for (const name of ['alert', 'badge', 'card', 'table', 'spinner', 'sheet']) overrides[`@/components/ui/${name}`] = ui;
  overrides['next/link'] = { __esModule: true, default: ({ href, children }) => React.createElement('a', { href }, children) };
  overrides['@/components/ui/button'] = { Button: button };
  const { default: HomePage } = loadTs('src/app/page.tsx', overrides);
  const booking = { loadId: 'LD09001', version: 1, state: 'RESERVED', cohort: 'real', mc: '138328', rate: 1900, load: null, events: [] };
  const good = (row) => ({ ok: true, snapshot: { liveBooking: true, generatedAt: '2026-11-03T12:00:00Z',
    kpis: { calls: 1, codePassed: 1, handoffs: 1, northstar: 1, repConfirmed: 0, tmsAcknowledged: 0, tmsConfirmed: 0, unknown: 0, outcomes: {}, medianSecondsToFirstOffer: 0, closedWithSummary: 0, endsReported: 0, syntheticCalls: 0 }, turnedAway: [], calls: [], bookings: [row] } });
  let tree;
  const visible = () => JSON.stringify(tree.toJSON()).includes('Keep this copy');
  try {
    snapshot = { ok: false, status: 503 };
    await act(async () => { tree = Renderer.create(await HomePage()); });
    assert.equal(timers.size, 1);
    assert.ok(tree.root.findAllByType('button').some((b) => b.children.includes('Refresh')));
    snapshot = good(booking);
    await act(async () => { tree.update(await HomePage()); });
    await act(async () => { tree.root.findAllByType('button').find((b) => b.children.includes('Confirm')).props.onClick(); });
    snapshot = good({ ...booking, state: 'SUBMITTING', version: 2 });
    await act(async () => { tree.update(await HomePage()); });
    await act(async () => { resolveFetch({ ok: true, json: async () => ({ status: 'receipt_not_saved', state: 'ACK_PENDING', reference: 'FIXTURE', rawReply: 'STATUS:PENDING' }) }); });
    assert.equal(backing.size, 1);
    assert.ok(visible());
    await act(async () => { tree.update(await HomePage()); });
    assert.ok(visible());
    await act(async () => { tree.unmount(); tree = Renderer.create(await HomePage()); });
    assert.ok(visible());
    snapshot = { ok: false, status: 503 };
    await act(async () => { tree.update(await HomePage()); });
    assert.ok(visible());
    assert.equal(timers.size, 1);
    const before = refreshes;
    await act(async () => { for (const fn of timers.values()) fn(); });
    assert.ok(refreshes > before);
  } finally {
    if (tree) await act(async () => tree.unmount());
    delete global.window; delete global.document; delete global.fetch;
  }
});

test('mobile state follows media changes and removes its listener on unmount', async () => {
  const listeners = new Set();
  let matches = false;
  global.window = { matchMedia: () => ({ matches, addEventListener: (_, fn) => listeners.add(fn), removeEventListener: (_, fn) => listeners.delete(fn) }) };
  const { useIsMobile } = loadTs('src/hooks/use-mobile.ts');
  const Probe = () => React.createElement('span', null, useIsMobile() ? 'mobile' : 'desktop');
  let tree;
  try {
    await act(async () => { tree = Renderer.create(React.createElement(Probe)); });
    assert.equal(tree.toJSON().children[0], 'desktop');
    matches = true;
    await act(async () => { for (const fn of listeners) fn(); });
    assert.equal(tree.toJSON().children[0], 'mobile');
  } finally {
    if (tree) await act(async () => tree.unmount());
    assert.equal(listeners.size, 0);
    delete global.window;
  }
});

test('disabled Confirm cannot send, while Decline stays available', async () => {
  let sends = 0;
  global.fetch = async () => { sends++; return { ok: true, json: async () => ({ status: 'released' }) }; };
  global.window = { confirm: () => { throw new Error('Disabled Confirm opened its prompt'); } };
  const overrides = { 'next/navigation': { useRouter: () => ({ refresh() {} }) },
    sonner: { toast: { success() {}, error() {} } }, '@/components/ui/button': { Button: button }, '@/components/ui/spinner': ui };
  const { RepActions } = loadTs('src/components/rep-actions.tsx', overrides);
  let tree;
  try {
    await act(async () => { tree = Renderer.create(React.createElement(RepActions, {
      loadId: 'LD09001', version: 1, actions: ['confirm', 'decline'], confirmText: 'Fixture', confirmDisabledReason: 'Sends off',
    })); });
    const buttons = tree.root.findAllByType('button');
    const confirm = buttons.find((b) => b.children.includes('Confirm'));
    const decline = buttons.find((b) => b.children.includes('Decline'));
    assert.equal(confirm.props.disabled, true);
    assert.equal(decline.props.disabled, false);
    await act(async () => { confirm.props.onClick(); });
    assert.equal(sends, 0);
    await act(async () => { decline.props.onClick(); });
    assert.equal(sends, 1);
  } finally {
    if (tree) await act(async () => tree.unmount());
    delete global.window; delete global.fetch;
  }
});
