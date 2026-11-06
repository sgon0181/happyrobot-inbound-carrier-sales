# Onboarding

The current candidate is [Carrier Sales Build 10](https://carrier-sales-proposal-sg.happyrobot.dev/), backed by the isolated proposal service and Twin staging. Voice Version 15 runs in workflow Development. Start with [readiness and one-command setup](readiness.md), then the architecture and decisions below. The original main/App/voice release is preserved separately.

Updated 2026-11-05 (Australia/Sydney). A clone includes tracked source and sanitized evidence, not browser sessions, local `.env`, private recordings or MCP authentication. Use `make review` for a complete disposable local App without those credentials.

## Read first

1. [`../AGENTS.md`](../AGENTS.md): who writes, how work is reviewed, and the writing rule.
2. [`../ARCHITECTURE.md`](../ARCHITECTURE.md): how the system works.
3. [`decisions.md`](decisions.md): why it works that way, and what is still open.
4. [`assignment.md`](assignment.md) and the [assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf): requirements and deliverables.
5. [`questions.md`](questions.md): Luke's November 5 acceptance of the PENDING handling, ZIP submission route, reviewer timing and sandbox inventory limits of evidence.
6. [`tms/README.md`](tms/README.md) and [`tms-contract.md`](tms-contract.md): protocol usage, live observations and spent inventory.

Keep requirements, observed behaviour, assumptions and simulations distinct. The handbook is a field manual with sample transcripts, and a live discrepancy must be recorded with its scope. Reading `PENDING` as any particular business stage is an interpretation, not a confirmed contract.

## Local change awaiting review and publication

The reciprocal negotiation policy and voice prompt draft v16 are local only. See [negotiation review](negotiation-review.md) for exact policy, results and required `negotiations` table. The live candidate and Version 15 described below remain unchanged.

## Current state

| Area | State |
|---|---|
| `ultimateProposal` | Current reviewed candidate source, isolated App Build 10 and proposal service; voice V15 in Development. Readiness records 563 service tests, 65 App tests, raw 71/74 native checkpoints and three overlapping actual diagnostic-caller audio scenarios. The owner still records a new human call and final video. |
| `main` | Preserved at 15ce2b6 with the original submission ZIP. App Build 24, voice Version 8 and service release 17 remain the baseline. No proposal merge or baseline replacement is implied. |
| `prototype/e2e` | Working system at `4b5ef3a`. Reference only. Not merged. See [lessons](lessons-from-prototype.md). |
| `lab/harness-v24` | Earlier Codex test harness, kept locally. Historical. |
| Who does what | One assigned writer at a time, followed by independent read-only review. The owner authorized reviewed proposal-branch pushes; production promotion and final portal submission remain separate decisions. |
| Spent loads | Listed in [`tms-contract.md`](tms-contract.md#booking-test-inventory) and [`blocked-loads-v1.json`](../service/policy/blocked-loads-v1.json). No supported cancel/reset is established; no quota or permanent-consumption claim follows. |

Workspace: [FDE - Santiago Gonzalez Alvarez](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez), organization ID `01a17a99-0856-7f88-b09f-4b787e20413c`.

| Platform resource | Identity | State |
|---|---|---|
| Preserved workflow Production | Inbound Carrier Sales, `01a18119-67a1-79a3-b220-369aa359d4fb`, slug `6oaskq84xpfc` | Version 8 (`kvexhw5fzj4y`, UUID `01a1a4f6-79a3-7c40-8732-589b3adfdcfd`) live since 2026-11-04, replacing Version 7. Prompt SHA-256: `53a884aea629114fa6d3342b9c8cf9f392bf376ca053622ab1f561821d33437c`. |
| Prototype workflow | `01a19476-5384-704b-9c5e-569fd96f9adf`, slug `yhcdrf4kne4j` | Historical owner-call evidence retained; unpublished on 2026-11-04. |
| Preserved Operations App | Carrier Sales; existing slug `codex-lab-carrier-sales-v24`, alias `carrier-sales-santiago.happyrobot.dev` | Published Build 24 serves Reservations, Overview, Bookings, Calls and Demand at the alias. Reviewed Build 23 introduced the reconciled voice sample. Booking sends remain off. See [dashboard release](releases/2026-11-04-dashboard-clarity/README.md). |
| Prototype service | Fly app `codex-e2e-lab-sg-20261031`, `iad` | Stopped, bookings off. |
| Prototype Twin tables | `proto_*` | Keep until the build no longer needs them. |
| Baseline Twin production tables | `calls`, `bookings`: `id` text primary key, `version` int, `data` jsonb | Created on 2026-11-02. Schema checked, and version-checked writes proven from Fly on 2026-11-03 (T-1). |

### Candidate resources

| Resource | Current isolated target |
|---|---|
| Native App | [Carrier Sales Candidate Build 10](https://carrier-sales-proposal-sg.happyrobot.dev/), its own Apps Production hosting slot |
| Service | `happyrobot-proposal-sg`, https://happyrobot-proposal-sg.fly.dev; final accepted runtime and policy hashes in [deployment evidence](evidence/readiness/deployed-service.json) |
| Workflow Development | Same workflow `6oaskq84xpfc`, Version 15, slug `4l79y6ugq62q`; [exact prompt and acceptance](readiness.md#native-conversation-evidence) |
| Twin staging | Separate `calls` and `bookings`, same schema; imported history is immutable. `TWIN_ENVIRONMENT=staging`, `CALL_COHORT=synthetic`, `LIVE_BOOKING=false` |

The App hosting slot, workflow environment and Twin environment are different controls. Candidate App Production does not mean production voice or production data. The [validated LD01123 agreement](https://carrier-sales-proposal-sg.happyrobot.dev/?view=reservations&load=LD01123&run=8eb82ad6-79b8-4c11-94ab-99bd1ce34c9b) links the actual development run. No real booking send was made during this acceptance.

### Historical release observations

After owner approval, Claude reports pushing `bf512aa`, deploying Fly release 17, then publishing Version 6. Codex independently verified GitHub main, 28 matching deployed runtime source/policy files, the healthy machine, authenticated health/snapshot reads, missing-key 401 on `/calls/ended`, and the exact live prompt. At that earlier release check, the native App selector showed production Build 20; source 48ba398/import 97da4f6 is reported in Claude's release handover, the 77-file archive matches the checkout, and the final visual check passes. See [release verification](releases/2026-11-04-v6/README.md). LIVE_BOOKING remains false and CALL_COHORT remains synthetic. Six test reservations were declined on 2026-11-04. Committing later documentation does not deploy it. The repository privacy/access check from 2026-11-03 found only the owner and zero pending invitations; that was an access snapshot. Luke later accepted a portal ZIP without a prior GitHub invitation.

Historical Version 7 publication matched reviewed 9d7a149. Version 8 subsequently replaced it under the owner's non-portal release approval, with exact post-publication root and tool readbacks matching eaa2661. No service deployment, App publication or secret change was needed. See releases/2026-11-04-v8/README.md. The owner withdrew portal-writing authorization and handles final submission alone. Do not open, fill, upload to or submit through the portal. If the private-link alternative is chosen, Luke can provide the reviewer account after submission. HappyRobot workspace access is separate.

Refresh this before relying on it. Do not edit a published workflow version, or reconstruct editor URLs.

## Setup for the current candidate

For a fresh reviewer machine with Docker Compose and Python 3.12, run `make review` from the root. It builds and opens the full local App with fixture identity, service, email, Twin and TCP TMS. Confirm changes one fixture booking to PENDING; `make review-down` removes only this disposable environment. No customer credentials or cloud writes are needed.

Cloud resources listed above already exist. Do not recreate or overwrite them. For a new isolated deployment:

1. Provision separate Twin staging `calls` and `bookings` with `id` text primary key, `version` int and `data` jsonb. The API cannot create tables. Leave production and prototype tables alone.
2. Use an authorized Editor API key for the service; scopes are workspace-wide while tag scopes are off. Configure the isolated Fly target and native App/workflow separately.
3. Generate distinct service agent/ops keys and OTP/pricing secrets into protected settings. Set the staging environment, synthetic cohort and sends off. Set the App's exact canonical origin, service URL and explicit rep subjects; configure trusted workflow provenance. The [pilot settings](proposal.md#pilot-configuration-and-rollback) define these boundaries and enrolled contacts for any future send-enabled deployment.
4. With the intended target and matching readiness key available, run `make secrets APP=<isolated-fly-app> APP_URL=<native-app-https-url>`, then `make deploy APP=<isolated-fly-app> APP_URL=<native-app-https-url>`. The first stages allowlisted settings; the second deploys, verifies authenticated health and TMS reachability, then opens the App. There is no implicit cloud target. Neither command provisions or publishes native resources.
5. Configure approved email delivery for the demonstration. A customer pilot requires independently enrolled carrier contacts and shared throttling. The shared inbox cannot authorize a real booking.

`make run` remains a service-only container command using deliberately supplied `.env`; it is not the full reviewer App. Exact tested commands, source manifests and limits are in [readiness](readiness.md#reproduce-the-application).

## Access without committing secrets

The private candidate portal link is in Luke's original "HappyRobot | FDE Technical Challenge" email. It carries credentials, so never copy it, invitation tokens or portal HTML into Git.

| System | Access |
|---|---|
| Legacy TMS | The portal supplies host, port and candidate token. Put them in the ignored `.env`, from [`.env.example`](../.env.example). |
| Handbook | The [manual](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/) uses a password form. `TMS_DOCS_PASSWORD` is separate from the TMS token. |
| HappyRobot MCP | Each coding client has its own OAuth login, at `https://mcp.platform.happyrobot.ai/workflows/mcp`. Discover integration events and schemas; do not guess IDs. |
| FMCSA | Use the portal-issued key. Direct requests work from Fly.io and return HTTP 403 from the local machine. |
| Twin | External SQL needs an organization API key. A Viewer key cannot write. The Apps gateway to Twin has been failing (T-7), so the app reads through the service. |
| OTP email | Luke approved email to the candidate's demo inbox. `DEMO_OTP_EMAIL` is configuration, never caller input, and is not proof of carrier identity. |
| Fly.io | Candidate: `happyrobot-proposal-sg`. Preserved baseline: `happyrobot-carrier-sales-sg`, one machine in `iad`, release 17 verified November 4. CLI authentication is local and is not part of a clone. Select the target explicitly. |

Local credentials are not part of a clone. Use the owner-managed ignored .env and platform secret settings; do not assume an old prototype worktree is the current source. This documentation pass does not re-inspect secret values or change configuration. Never copy credential values into documentation, prompts or commits. `.gitignore` prevents commits, not access, so keep raw studies, codes, ceilings and credentials out of runtime voice context.

## FMCSA integration starting point

Official [Quick Start](https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted) and [API reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi). The docket lookup used:

```text
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/<MC_DIGITS>/?webKey=<FMCSA_API_KEY>
```

Never log the full URL, because it contains `webKey`. A returned record or HTTP 200 alone does not establish eligibility. The rule is in [architecture section 8](../ARCHITECTURE.md#8-verification-and-the-one-time-code), and checked carriers are in the [ledger](test-carriers.md).

## Keeping this true

Update this page, the architecture and the decisions log together when real state changes. A local commit is visible only in this checkout until the owner approves a push.
