# Onboarding

Start with [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview), [release readiness](release.md), [architecture](architecture.md) and [decisions](decision-log.md). `main` is the submission source. The assignment PDF in `docs/` remains the requirements source; [assignment.md](assignment.md) summarizes it.

## Read first

Read [`AGENTS.md`](../../AGENTS.md) before changing source. One assigned writer changes tracked files, followed by review. Read [the TMS reference](../tms/README.md) and [contract observations](../tms-contract.md) before implementing or testing a TMS operation. The owner handles the final portal submission.

A clone includes source and sanitized evidence. It does not include browser sessions, private recordings, OAuth authentication or `.env` secrets. Use `make review` for a complete local App without cloud access.

## Current state

The service at `https://happyrobot-proposal-sg.fly.dev` serves the populated App. Twin staging retains the recorded history and fresh calls. Its `calls`, `bookings` and `negotiations` tables use `id` text primary key, `version` integer and `data` JSONB. The last release snapshot contained 74 call rows and 19 booking rows; this is a dated count, not a fixed dashboard population.

Version 19 (`l6zo75s4s4vk`, UUID `01a1b2ea-26c8-7131-8252-b334dcaab976`) is live in workflow Production. Use [the Production web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) and [its exact editor](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/l6zo75s4s4vk). Version 8 is retained unpublished for rollback. Development is empty. [Readiness](release.md#current-release-state) records acceptance, limitations and endpoints. Workflow Production, App hosting and Twin environment are separate controls.

The owner retained the approved demo email route, synthetic record tags and disabled hosted sends. See [the single explanation of this boundary](release.md#current-release-state). Historical imported records remain immutable; do not relabel them to enable a send.

## Platform resources

| Resource | Identity |
| --- | --- |
| Workspace | [FDE - Santiago Gonzalez Alvarez](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez) |
| Organization | `01a17a99-0856-7f88-b09f-4b787e20413c` |
| Workflow | Inbound Carrier Sales, `01a18119-67a1-79a3-b220-369aa359d4fb`, slug `6oaskq84xpfc` |
| App | [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/) |
| Service | Fly app `happyrobot-proposal-sg`, region `iad` |
| Data | Twin staging: `calls`, `bookings`, `negotiations` |
| Rollback | `oldmain` and local `baseline-v8` tag at `15ce2b6`; Version 8 and App Build 24 |

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

## Deployment and rollback

Use the explicit commands in [readiness](release.md#reproduce-the-application). Verify tables, authenticated health, TMS reachability, email route, tool bindings, App login and recording links before promoting the tested workflow. Review actual call endings and rates as well as grades. No cloud command creates the native App, workflow or Twin schema implicitly.

For rollback, restore the prior workflow Production version and prior service/App links as a coordinated release. Preserve new records and investigate uncertain TMS outcomes; never resend automatically. Main history and rollback refs remain available.

## History

Version 8 and Build 24 are the earlier demonstration. The prototype branch is historical reference only and is never merged. The recruiter accepted honest PENDING handling and a ZIP submission; see [questions](questions.md). The prior deployment and import manifests remain dated evidence in [readiness](release.md#history).
