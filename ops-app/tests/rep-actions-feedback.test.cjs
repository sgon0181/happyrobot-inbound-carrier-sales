const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const Renderer = require('react-test-renderer');
const loadTs = require('./load-ts.cjs');
const { act } = Renderer;
global.IS_REACT_ACT_ENVIRONMENT = true;

const cases = [
  ['nothing sent while building', { status: 'sent', state: 'FAILED', reason: 'not_sent' }, false, /No booking request was sent/],
  ['TMS refusal', { status: 'sent', state: 'FAILED', reason: 'invalid_rate' }, false, /TMS refused.*invalid_rate/],
  ['failed receipt without its reason', { status: 'sent', state: 'FAILED' }, false, /Booking failed.*Review the receipt/],
  ['uncertain send', { status: 'sent', state: 'UNKNOWN', reason: 'no_complete_reply' }, false, /outcome unknown.*Reconcile.*never resend/],
  ['pending acknowledgement', { status: 'sent', state: 'ACK_PENDING', tmsStatus: 'PENDING', reference: 'FIXTURE' }, true, /acknowledged.*pending.*not a final booking.*FIXTURE/],
  ['TMS confirmation', { status: 'sent', state: 'CONFIRMED', tmsStatus: 'BOOKED', reference: 'FIXTURE' }, true, /TMS confirmed.*BOOKED.*FIXTURE/],
  ['unrecognized receipt', { status: 'sent', state: 'NEW_STATE' }, false, /Unrecognized booking result.*NEW_STATE/],
  ['missing receipt state', { status: 'sent' }, false, /Unrecognized booking result.*not recorded/],
  ['unsaved no-send result', { status: 'receipt_not_saved', state: 'FAILED', reason: 'not_sent', sendStep: 'connect', rawReply: '', sendSha256: 'fixture-sha256' }, false, /No booking request was sent.*not saved.*Keep the copy/],
  ['unsaved pending result', { status: 'receipt_not_saved', state: 'ACK_PENDING', reference: 'FIXTURE', rawReply: 'LOAD_ID:LD09001|BOOKING_REF:FIXTURE|STATUS:PENDING\r\nEND\r\n', sendSha256: 'c'.repeat(64) }, false, /acknowledged.*pending.*not saved.*Keep the copy/],
  ['unsaved unknown result', { status: 'receipt_not_saved', state: 'UNKNOWN' }, false, /outcome unknown.*Reconcile.*never resend.*not saved.*Keep the copy/],
  ['unsaved confirmed result', { status: 'receipt_not_saved', state: 'CONFIRMED', tmsStatus: 'BOOKED', reference: 'FIXTURE' }, false, /TMS confirmed.*BOOKED.*not saved.*Keep the copy/],
  ['preflight rejected a non-open load', { status: 'failed', reason: 'load_not_open' }, false, /No booking request was sent.*load_not_open/],
  ['preflight found a lower ceiling', { status: 'failed', reason: 'ceiling_below_rate' }, false, /No booking request was sent.*ceiling_below_rate/],
  ['local release', { status: 'released' }, true, /Reservation released.*No booking request was sent/],
  ['read-only reconciliation', { status: 'reconciled', state: 'UNKNOWN', loadStatus: 'PENDING' }, true, /TMS shows.*PENDING.*UNKNOWN/],
  ['stale version', { status: 'stale' }, false, /changed since your screen loaded/],
  ['blocked state', { status: 'not_allowed', state: 'SUBMITTING' }, false, /Not available.*SUBMITTING/],
  ['disabled sends', { status: 'live_booking_off' }, false, /Live booking is off/],
  ['failed read', { status: 'tms_unavailable' }, false, /TMS could not be read.*Nothing was sent/],
  ['early reconciliation', { status: 'too_early' }, false, /Reconcile after a minute/],
  ['unrecognized service status', { status: 'new_status' }, false, /Service answered new_status/],
];

for (const [name, reply, success, expected] of cases) {
  test(`rep feedback: ${name}`, async () => {
    const messages = [], requests = [], receipts = [];
    let refreshes = 0;
    global.window = { confirm: () => true };
    global.fetch = async (url, options) => {
      requests.push({ url, options });
      return { ok: true, json: async () => reply };
    };
    const overrides = {
      'next/navigation': { useRouter: () => ({ refresh() { refreshes++; } }) },
      sonner: { toast: {
        success: (text) => messages.push({ success: true, text }),
        error: (text) => messages.push({ success: false, text }),
      } },
      '@/components/ui/button': { Button: ({ children, ...props }) => React.createElement('button', props, children) },
      '@/components/ui/spinner': { Spinner: () => null },
      '@/lib/unsaved-receipts': { keepReceipt: (...args) => receipts.push(args) },
    };
    const { RepActions } = loadTs('src/components/rep-actions.tsx', overrides);
    const action = reply.status === 'released' ? 'decline' : reply.status === 'reconciled' || reply.status === 'too_early' ? 'reconcile' : 'confirm';
    let tree;
    try {
      await act(async () => { tree = Renderer.create(React.createElement(RepActions, {
        loadId: 'LD09001', version: 17, actions: [action], confirmText: 'Fixture only',
      })); });
      await act(async () => { await tree.root.findByType('button').props.onClick(); });
      assert.equal(requests.length, 1);
      assert.equal(requests[0].url, `/api/bookings/LD09001/${action}`);
      assert.equal(requests[0].options.method, 'POST');
      assert.deepEqual(JSON.parse(requests[0].options.body), { version: 17 });
      assert.equal(messages.length, 1);
      assert.equal(messages[0].success, success);
      assert.match(messages[0].text, expected);
      assert.doesNotMatch(messages[0].text, /load is free|Sent once/);
      assert.equal(refreshes, 1);
      assert.equal(receipts.length, reply.status === 'receipt_not_saved' ? 1 : 0);
      if (receipts.length) {
        assert.equal(receipts[0][0], 'LD09001');
        const copy = JSON.parse(receipts[0][1]);
        for (const [key, value] of Object.entries(reply)) assert.equal(copy[key], value);
      }
    } finally {
      if (tree) await act(async () => tree.unmount());
      delete global.window;
      delete global.fetch;
    }
  });
}
