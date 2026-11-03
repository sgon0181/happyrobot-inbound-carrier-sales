// Renders the dashboard to static HTML from a saved snapshot, for a visual check without sign-in.
// Usage: node tests/preview.cjs <snapshot.json> <out-dir> <css-href>. Not part of the test suite.
const fs = require('node:fs');
const path = require('node:path');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const loadTs = require('./load-ts.cjs');

const [snapshotFile, outDir, cssHref] = process.argv.slice(2);
const { projectSnapshot } = loadTs('src/lib/snapshot.ts');
const snapshot = projectSnapshot(JSON.parse(fs.readFileSync(snapshotFile, 'utf8')));
const realOps = loadTs('src/lib/ops-service.ts');
const link = ({ href, children, ...props }) => React.createElement('a', { href, ...props }, children);
const overrides = {
  'next/navigation': { useRouter: () => ({ refresh() {} }), usePathname: () => '/' },
  'next/link': { __esModule: true, default: link },
  '@/lib/auth': { requireAppUser: async () => ({ user: {} }) },
  '@/lib/ops-service': { ...realOps, getSnapshot: async () => ({ ok: true, snapshot }) },
  '@/brand-assets/blacklogo.png': { __esModule: true, default: { src: 'logo.png' } },
  '@/brand-assets/blackicon.png': { __esModule: true, default: { src: 'icon.png' } },
};
const { default: HomePage } = loadTs('src/app/page.tsx', overrides);

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  for (const [name, params] of [
    ['overview-real', {}], ['overview-test', { scope: 'test' }], ['reservations-test', { view: 'reservations', scope: 'test' }],
    ['bookings-test', { view: 'bookings', scope: 'test' }], ['calls-test', { view: 'calls', scope: 'test' }], ['demand-test', { view: 'demand', scope: 'test' }],
  ]) {
    const body = renderToStaticMarkup(await HomePage({ searchParams: Promise.resolve(params) }));
    const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="stylesheet" href="${cssHref}"><style>:root{--font-sans:Inter,ui-sans-serif,system-ui,sans-serif}</style></head><body class="min-h-svh antialiased font-sans">${body}</body></html>`;
    fs.writeFileSync(path.join(outDir, `${name}.html`), html);
  }
  console.log('rendered', fs.readdirSync(outDir).length, 'pages');
})();
