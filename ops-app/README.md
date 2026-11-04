# Operations app

**Proposal checkout.** The [Friday pilot guide](../docs/proposal.md) identifies the branch changes, test evidence and deployment prerequisites. Hosted links and release descriptions below refer to the published baseline. The proposal voice candidate and App are separate from the published release.


For the proposal, configure server-only OPS_APP_ORIGIN, OPS_SERVICE_URL, OPS_API_KEY, and OPS_REP_SUBJECTS in the isolated App environment. The service URL has no implicit production fallback. See the [pilot runbook](../docs/proposal.md).

The dashboard for the operations manager and senior reps, built on the HappyRobot Apps Next.js template and mirrored here for review. It is described in [architecture section 11](../ARCHITECTURE.md#11-operations-app).

## How it works

The app verifies the signed-in user with the platform, then calls the service from its own server with the ops key ([D-30](../docs/decisions.md)). The key never reaches the browser, and the app never reads Twin or talks to the TMS. The service holds every rule; the app only shows its snapshot and forwards a rep's actions.

The default route is Reservations. Its current queue shows live service rows across deployment tags, most recent originating call first. The separate history includes each saved reservation, even when a later call reserved the same load. Open a review by its load and run ID. A stale owner link provides historical call evidence without controls for the current owner's reservation. The native recording link opens HappyRobot with the signed-in user's permissions.

- **Overview** (`/?view=overview`) uses 49 completed Native inbound sessions matched to Twin. Every funnel and exception count links to its calls. Opening and agreed price pairs and actual agent counteroffers are inspectable.
- **Bookings** lists submitted bookings and the TMS status and reference. Unknown or stale submissions open their own reconciliation record.
- **Calls** searches MC, carrier, load, lane, outcome and Central date range. It includes the originating run, pricing rounds, actual agent counteroffers and closing notes.
- **Demand** separates empty searches, verified calls without searches and other unsuccessful searches. Lanes use the final explicit empty search, once per call. An ambiguous legacy lane remains unrecorded.

The business formulas and reconciliation evidence are in [KPI definitions](../docs/kpis.md). The dated report, current open work and native evaluation results serve different purposes.

Each action posts the booking version the rep saw ([D-31](../docs/decisions.md)) to `/api/bookings/{load_id}/{action}`. That route takes the rep's identity from the verified session, never from the request, and forwards `{version, rep}` to the service. The rep sees the service's answer, such as `stale` when the row has moved on or `live_booking_off` when sends are disabled. If a send's receipt could not be saved, the whole receipt, raw bytes included, stays in a panel at the top of the page, and in the browser's storage, with Copy and Download, until the rep dismisses it. The panel and the refresh controls stay up even when the snapshot fails.

## Files

| Path | Origin |
|---|---|
| `src/lib/ops-service.ts`, `src/app/page.tsx`, `src/components/rep-actions.tsx`, `src/app/api/bookings/[loadId]/[action]/route.ts` | Written for this service's snapshot and rep actions |
| `src/lib/env.ts` | Template, plus `OPS_API_KEY` and `OPS_SERVICE_URL` |
| `package.json`, `package-lock.json` | Template, with `next` raised to 16.4.4 and `shadcn`, a build-time CSS import, moved to dev dependencies, so `npm audit --omit=dev` finds nothing |
| Everything else: sign-in, middleware, layout, UI components, config | The HappyRobot Apps template, unchanged from the prototype's `ops-app/` on `prototype/e2e` |

## Settings

| Name | Where | Meaning |
|---|---|---|
| `OPS_API_KEY` | App secret, server only | The service's ops key. Never `NEXT_PUBLIC`. |
| `OPS_SERVICE_URL` | App setting, required | The intended service's HTTPS address. |
| `HR_PLATFORM_URL`, `NEXT_PUBLIC_ORG_ID`, `NEXT_PUBLIC_APP_SLUG`, `NEXT_PUBLIC_APP_NAME` | Supplied by the platform | Sign-in and app identity, as in the template |

## Checks

Use Node 22 and `npm ci --include=dev`, then lint, production build, typecheck and `npm test`. The released source at `8b0e483` passes all 35 tests and those checks, with three existing lint warnings. The most recent production dependency audit reported zero vulnerabilities. Carrier Sales Build 18 was published and visually checked on 2026-11-04; see [QA results](../docs/qa-results.md).
