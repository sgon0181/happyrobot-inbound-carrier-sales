const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const ts = require('typescript');

function load(relative) {
  const source = fs.readFileSync(relative, 'utf8');
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  });
  const loaded = { exports: {} };
  new Function('module', 'exports', 'require', outputText)(loaded, loaded.exports, require);
  return loaded.exports;
}
const { events } = load('src/lib/event-history.ts');

test('projects actual public_view strings, pitch details and search criteria', () => {
  const [event] = events([{
    seq: 1, action: 'find_loads', status: 'found',
    search: { equipment: 'DRY_VAN', origin_state: 'TX', dest_state: 'GA' },
    loads: [{ load_id: 'LD09001', origin: 'Dallas, TX', destination: 'Atlanta, GA',
      offer: 1900, pickup_datetime: '2099-12-31T08:00:00+00:00', weight: 42000,
      notes: 'Appointment required', max_rate: 9876543 }],
  }]);
  for (const value of ['Dallas, TX', 'Atlanta, GA', '1900', '42000', 'Appointment required', 'DRY_VAN / TX / GA']) {
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
  assert.match(history[0].detail, /carrier said 5,000, ask 5000/);
  assert.match(history[1].detail, /ask 5100/);
  assert.match(history[2].detail, /ended by user, seconds 52/);
  assert.ok(!JSON.stringify(history).includes('private-'));
});
