# Operations app

The dashboard for the operations manager and senior reps, built on the HappyRobot Apps Next.js template and mirrored here for review. It is described in [architecture section 11](../ARCHITECTURE.md#11-operations-app).

## How it works

The app verifies the signed-in user with the platform, then calls the service from its own server with the ops key ([D-30](../docs/decisions.md)). The key never reaches the browser, and the app never reads Twin or talks to the TMS. The service holds every rule; the app only shows its snapshot and forwards a rep's actions.

- **Overview:** the KPIs from `GET /ops/snapshot`, real calls only, with outcome counts and the number of test calls left out. The page refreshes every 15 seconds while visible, with Refresh and Pause controls, so new reservations and Reconcile after a minute appear on their own.
- **Reservations awaiting a rep:** `RESERVED` bookings, with Confirm and Decline. Confirm asks once more, because it spends the load.
- **Sent and closed bookings:** the booking state, the TMS status and reference exactly as returned, the send evidence (step, error, bytes, sha256) and the events. `ACK_PENDING` and `UNKNOWN` offer Reconcile, as does a `SUBMITTING` row older than a minute.
- **Call log:** each call's derived outcome, rounds, summary and events, with each event's MC, load, rate, offers and round.
- **Turned-away demand:** lanes asked for when nothing matched.
- **Test bookings and calls:** the synthetic cohort, shown apart.

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
| `OPS_SERVICE_URL` | App setting, optional | The service's HTTPS address. Defaults to `https://happyrobot-carrier-sales-sg.fly.dev`. |
| `HR_PLATFORM_URL`, `NEXT_PUBLIC_ORG_ID`, `NEXT_PUBLIC_APP_SLUG`, `NEXT_PUBLIC_APP_NAME` | Supplied by the platform | Sign-in and app identity, as in the template |

## Checks

Use Node 22 and `npm ci --include=dev`, then lint, production build, typecheck and `npm test`. The released source at `8b0e483` passes all 35 tests and those checks, with three existing lint warnings. The most recent production dependency audit reported zero vulnerabilities. Carrier Sales Build 18 was published and visually checked on 2026-11-04; see [QA results](../docs/qa-results.md).
