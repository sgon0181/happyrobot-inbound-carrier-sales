# Operations app

Current candidate: [Carrier Sales Build 10](https://carrier-sales-proposal-sg.happyrobot.dev/), in its own Apps Production hosting slot, backed by the isolated service and Twin staging. Voice V15 uses workflow Development. The original App Build 24 remains unchanged. [Readiness](../docs/readiness.md) records accepted source/hosting evidence and the subsequent README-only divergence; executable App files are unchanged.

For the proposal, configure server-only OPS_APP_ORIGIN, OPS_SERVICE_URL, OPS_API_KEY, and OPS_REP_SUBJECTS in the isolated App environment. The service URL has no implicit production fallback. See the [pilot runbook](../docs/proposal.md).

The dashboard for the operations manager and senior reps, built on the HappyRobot Apps Next.js template and mirrored here for review. It is described in [architecture section 11](../ARCHITECTURE.md#11-operations-app).

## How it works

The app verifies the signed-in user with the platform and normalizes the returned native `id` into its internal subject. A legacy `sub` is accepted only when valid and consistent with `id`; missing, malformed or conflicting identity is refused. Decoded token claims never authorize a rep. The app then calls the service from its own server with the ops key ([D-30](../docs/decisions.md)). The key never reaches the browser, and the app never reads Twin or talks to the TMS. The service holds every rule; the app only shows its snapshot and forwards a rep's actions.

The default route is Reservations. Its current queue shows live service rows across deployment tags, most recent originating call first. The default list includes every saved agreement, even when a later call reserved the same load. Awaiting rep is a filter on that shared workspace. Imported historical rows are view-only. Open a review by its load and run ID. A stale owner link provides historical call evidence without controls for the current owner's reservation. The native recording link opens HappyRobot with the signed-in user's permissions. New runs require immutable trusted workflow provenance; fixtures without it have no guessed media link.

- **Overview** (`/?view=overview`) deduplicates UUID-shaped call records from the complete bounded snapshot, without a fixed 49-run limit. This format admission is not independent platform attestation; historical native inventory enriches known duration and end evidence. Ongoing calls contribute stage progress but never enter ended-call loss groups. Funnel stages and exception groups link to their calls. Opening and agreed price pairs and actual agent counteroffers are inspectable.
- **Bookings** lists submitted bookings and the TMS status and reference. Unknown or stale submissions open their own reconciliation record.
- **Calls** searches MC, carrier, load, lane, outcome and Central date range. It includes the originating run, pricing rounds, actual agent counteroffers and closing notes.
- **Demand** separates empty searches, verified calls without searches and other unsuccessful searches. Lanes use the final explicit empty search, once per call. An ambiguous legacy lane remains unrecorded.

The business formulas and reconciliation evidence are in [KPI definitions](../docs/kpis.md). The unified operational report and native behavioral evaluations serve different purposes. The App gives snapshot reads twenty seconds and retains the current screen during a pending refresh. Refreshes never overlap; exhausting the budget shows unavailable, not partial data.

Each action posts the booking version the rep saw ([D-31](../docs/decisions.md)) to `/api/bookings/{load_id}/{action}`. That route requires an exact assigned `OPS_REP_SUBJECTS` identity and an allowed request Origin. It takes the rep's identity from the verified session, never from the request, and forwards `{version, rep}` to the service. The rep sees the service's answer, such as `stale` when the row has moved on or `live_booking_off` when sends are disabled. If a send's receipt could not be saved, its safe identifiers, status and digest stay in a panel and browser storage with Copy and Download until the rep dismisses it. Raw wire bytes do not reach the browser. The panel and the refresh controls stay up even when the snapshot fails.

## Files

| Path | Origin |
|---|---|
| `src/lib/ops-service.ts`, `src/app/page.tsx`, `src/components/rep-actions.tsx`, `src/app/api/bookings/[loadId]/[action]/route.ts` | Written for this service's snapshot and rep actions |
| `src/lib/env.ts` | Template, plus `OPS_API_KEY` and `OPS_SERVICE_URL` |
| `package.json`, `package-lock.json` | Template, with `next` raised to 16.4.4 and `shadcn`, a build-time CSS import, moved to dev dependencies, so `npm audit --omit=dev` finds nothing |
| Sign-in, middleware, layout and UI components | Based on the HappyRobot Apps template, with canonical-origin and rep-authorization hardening in this proposal |

## Settings

| Name | Where | Meaning |
|---|---|---|
| `OPS_API_KEY` | App secret, server only | The service's ops key. Never `NEXT_PUBLIC`. |
| `OPS_SERVICE_URL` | App setting, required | The intended service's HTTPS address. |
| `OPS_APP_ORIGIN` | App setting, server only | Exact canonical HTTPS origin; do not infer it from arbitrary forwarded headers. |
| `OPS_REP_SUBJECTS` | App secret, server only | Comma-separated platform-verified subjects authorized to mutate. Other users are viewers. |
| `ALLOWED_ORIGINS` | App setting, server only | Only explicit trusted HTTPS origins for a verified embed, when required. |
| `HR_PLATFORM_URL`, `NEXT_PUBLIC_ORG_ID`, `NEXT_PUBLIC_APP_SLUG`, `NEXT_PUBLIC_APP_NAME` | Supplied by the platform | Sign-in and app identity, as in the template |

Run the complete disposable App locally with `make review` from the repository root. [Readiness setup](../docs/readiness.md) describes credentials, cloud deployment and isolation.

## Checks

Use Node 22 and `npm ci --include=dev`, then `npm test`, `npm run lint`, `npm run build` and `npm run typecheck`. The accepted candidate passed 65 tests, production build and type checks; lint had zero errors and three existing warnings. Native hosted acceptance verified all 91 source files and the real platform identity contract. The local full-App browser test confirmed one simulated PENDING receipt, a safe stale replay and viewer denial. Hosted checks did not send a real booking. [Current QA and historical release evidence](../docs/qa-results.md) keep those scopes separate.
