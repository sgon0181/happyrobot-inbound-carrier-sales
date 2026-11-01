# Carrier Sales Prototype App

Sanitized native HappyRobot Apps source mirror. Source commit
`b2fd1638705e6cf4c25da0cac4073b89e1dac5e6`, exported from the approved app
`codex-lab-carrier-sales-v24` on 2026-11-01. One copied comment in .gitignore
was normalized to comply with the repository punctuation rule.

The App verifies HappyRobot sign-in and calls the service from its server.
There are no direct Twin business-data reads or writes. OPS_API_KEY belongs
only in the native App's server environment. It is never a public variable.
The platform supplies the existing HR_PLATFORM_URL, organization, App identity
and token-environment configuration. No credential file is included here.

Use Node 22 and npm ci. Run npm run build first in a fresh export so Next.js
generates next-env.d.ts, then npm run typecheck. Native template lint has a
known circular configuration failure, recorded in the prototype report.

The real call is in caller-consent review. Do not confirm it. Synthetic queue
fixtures are clearly labelled and excluded from real KPIs. A local rep decision
does not change the TMS from PENDING to BOOKED.

See the root PROTOTYPE_REPORT.md and docs/qa-results.md for measured outcomes
and the failed clean-run consent gate. This source mirror is for review;
publishing uses the native App deployment controls, not a Tech-Challenge push.
