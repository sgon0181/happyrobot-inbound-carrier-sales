# Carrier Sales App source mirror

Base source: native HappyRobot Apps commit
b2fd1638705e6cf4c25da0cac4073b89e1dac5e6, exported on 2026-11-01.
The candidate overlay changes only src/app/page.tsx and
src/components/app-sidebar.tsx to exactly match native sandbox commit
e6766e64915e4a4069253fb28fbb7d358c8d6b79. Both SHA256 hashes are verified in
[the source evidence](../docs/prototype-evidence/candidate-app-source.json).
One earlier copied .gitignore comment was normalized for the punctuation rule.

The existing App is codex-lab-carrier-sales-v24, now named HappyRobot Logistics
Carrier Sales, with saved alias https://carrier-sales-santiago.happyrobot.dev.
Its original URL stays active. The newer UI source is not published: native
Production deployment explicitly merges the separate App branch into main, so
it was canceled under the owner's hard limit. The prior functional dashboard
remains deployed. This mirror makes the candidate UI reviewable locally.

The App verifies HappyRobot sign-in and calls the service from its server.
No direct Twin business-data read or write remains. OPS_API_KEY is server-only.
The platform supplies HR_PLATFORM_URL, organization, App identity and token
configuration. This mirror contains no credential file.

Use Node 22 and npm ci. Run npm run build in a fresh export to generate
next-env.d.ts, then npm run typecheck. The native builder reports both passed
for the candidate, along with action-gate, redaction and sorting checks.
The template lint configuration has a known circular failure, retained in QA.

LD01094 specifically remains blocked for caller-consent review. Never confirm
that booking. UNKNOWN also has no Confirm action. Other valid pending receipts
can receive a local rep decision, which never changes the external TMS to BOOKED.
Real and synthetic cohorts remain separate.

Read [the report](../PROTOTYPE_REPORT.md) and [QA](../docs/qa-results.md) for the
actual final run. Publishing the App source remains a separate owner-reviewed
native deployment decision; no Tech-Challenge push is authorized here.
