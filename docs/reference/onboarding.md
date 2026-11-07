# Onboarding

Start with [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview), [release readiness](release.md), [architecture](architecture.md) and [decisions](decision-log.md). `main` is the submission source. The assignment PDF in `docs/` remains the requirements source; [assignment.md](assignment.md) summarizes it.

## Read first

Read [`AGENTS.md`](../../AGENTS.md) before changing source. One assigned writer changes tracked files, followed by review. Read [the TMS reference](../tms/README.md) and [contract observations](../tms-contract.md) before implementing or testing a TMS operation. The owner handles the final portal submission.

A clone includes source and sanitized evidence. It does not include browser sessions, private recordings, OAuth authentication or `.env` secrets. Use `make review` for a complete local App without cloud access.

## Current state

The service at `https://happyrobot-proposal-sg.fly.dev` serves the populated App. Twin staging retains the recorded history and fresh calls. Its `calls`, `bookings` and `negotiations` tables use `id` text primary key, `version` bigint and `data` JSONB. The dated population and state counts are in [results](../results.md#version-20-release-acceptance); the dashboard reads current records.

Version 20 (`zynb7wm66n9w`, UUID `01a1b3cf-1025-7c0f-91b6-75f57ce017b4`) is live in workflow Production. Use [the Production web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) and [its exact editor](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w). Version 19 is retained as the immediate non-live workflow rollback. Development is empty. [Readiness](release.md#current-release-state) records acceptance, limitations and endpoints. Workflow Production, App hosting and Twin environment are separate controls.

The owner retained the approved demo email route, synthetic record tags and disabled live carrier booking, then authorized a temporary challenge-sandbox Confirm window for the demo MC. See [the single explanation of this boundary](release.md#current-release-state). Historical imported records remain immutable; do not relabel them to enable a send.

## Platform resources

| Resource | Identity |
| --- | --- |
| Workspace | [FDE - Santiago Gonzalez Alvarez](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez) |
| Organization | `01a17a99-0856-7f88-b09f-4b787e20413c` |
| Workflow | Inbound Carrier Sales, `01a18119-67a1-79a3-b220-369aa359d4fb`, slug `6oaskq84xpfc` |
| App | [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/) |
| Service | Fly app `happyrobot-proposal-sg`, region `iad` |
| Data | Twin staging: `calls`, `bookings`, `negotiations` |
| Rollback | Immediate workflow rollback: Version 19. Historical source baseline: `oldmain` and local `baseline-v8` at `15ce2b6`, Version 8 and App Build 24 |

Do not edit a published workflow version or guess an editor URL. Read the exact version and URL from the native platform before making changes. Preserve original evidence files and record later results separately.

## Setup for a reviewer

With Docker Compose and Python 3.12, run `make review`. It builds and opens the authenticated App with a disposable reservation, identity provider, mailbox and TCP TMS. Confirm produces one simulated PENDING receipt. `make review-down` removes only this local environment.

For source checks, create a Python 3.12 virtual environment, install `requirements-dev.txt`, then run `make check`. In `ops-app`, use Node 22 and `npm ci`, followed by lint, test, production build and typecheck. Use `NODE_ENV=production` for the build.

## Access without committing secrets

| System | Setup |
| --- | --- |
| Legacy TMS | The challenge supplies host, port and token. Keep them in the ignored `.env` or service secrets. |
| Handbook | Its password is separate from the TMS token. Read tracked observations first. |
| FMCSA | Use the challenge key. Requests work from Fly `iad`; local requests were observed returning HTTP 403. |
| HappyRobot | Use the connected OAuth tools. An organization key with write scope is needed for service Twin writes. |
| Email | SMTP settings and the fixed demo destination are private configuration, never caller-supplied. |
| App | Server-only `OPS_SERVICE_URL`, matching `OPS_API_KEY`, exact `OPS_APP_ORIGIN` and explicit `OPS_REP_SUBJECTS`. |
| Fly | Always select `happyrobot-proposal-sg` explicitly for this release. The old `fly.toml` default is a rollback resource. |

`.env.example` lists settings. Only `service/config.py` reads runtime configuration. Never print secret values, put them in URLs or copy them into prompts or evidence. App keys must never use a `NEXT_PUBLIC` name. Native user identity is verified by the platform before rep authorization.

## Reproduce the Twin tables

The checked-in [bootstrap SQL](../../tools/twin-schema.sql) matches the observed table shape. In a **new** Twin workspace, select the intended environment in the SQL console and execute each statement separately. `IF NOT EXISTS` preserves existing tables and data; it does not repair an incompatible table. Do not run a reset, drop, truncate or historical import on the populated submission database.

With the organization key and ID in the ignored `.env` or environment, run this read-only check from the repository root:

```bash
python -m tools.check_twin_schema --environment staging
```

Choose `production` explicitly for a separately provisioned production database. The environment header selects the active schema; the check uses `current_schema()` so it does not accidentally inspect `public` when the service uses `staging`. It verifies column types, the single-column primary keys and compatibility of any extra columns, without reading call contents. Version and data columns match the existing nullable schema; service writes supply both. It does not assert data integrity or migrate anything.

The SQL gateway behavior observed for this integration and our four-statements-per-second pacing budget are not claims about every Twin interface. See [HappyRobot's SQL guidance](https://docs.happyrobot.ai/twin/sql-console-and-capacity) and [App/database setup guidance](https://docs.happyrobot.ai/twin/using-in-apps). No workflow run-dump table replaces the in-call application writes.

## Deployment and rollback

Use the explicit commands in [readiness](release.md#reproduce-the-application). Verify tables, authenticated health, TMS reachability, email route, tool bindings, App login and recording links before promoting the tested workflow. Review actual call endings and rates as well as grades. No cloud command creates the native App, workflow or Twin schema implicitly.

For rollback, restore the prior workflow Production version and prior service/App links as a coordinated release. Preserve new records and investigate uncertain TMS outcomes; never resend automatically. Main history and rollback refs remain available.

## History

Version 8 and Build 24 are the earlier demonstration. The prototype branch is historical reference only and is never merged. The recruiter accepted honest PENDING handling and a ZIP submission; see [questions](questions.md). The prior deployment and import manifests remain dated evidence in [readiness](release.md#history).

## Temporary challenge sandbox Confirm

The hosted send mode is recorded in [the release guide](release.md). To prepare a narrowly authorized demo, keep `LIVE_BOOKING=false` and configure `SANDBOX_BOOKING_MC`, `SANDBOX_BOOKING_SINCE` and `SANDBOX_BOOKING_UNTIL` in the service secret store. The timestamps must be UTC and the window may be at most 48 hours. Use the shortest practical recording window. This deliberately permits any otherwise eligible call for that MC inside the window, not only one run.

Startup also requires the assignment's exact TMS endpoint (`tramway.proxy.rlwy.net:17159`), Twin staging, synthetic calls and no contact roster. An endpoint change requires a reviewed policy change. Code verification still runs against the demo inbox. The source call and its current reservation event must both fall inside the window; recent edits do not authorize old holds. Rep sign-in, completed consent, shipment and ceiling rechecks, and one-shot submission remain mandatory. Remove the three settings or let the window expire to disable new sandbox sends. Receipt saving and reconciliation continue after expiry. No stored record should be changed to make it eligible.
