# Onboarding

[Reservations](https://carrier-sales-santiago.happyrobot.dev/) opens the rep's queue. Search by MC, carrier, load or lane and open [the filmed Werner agreement](https://carrier-sales-santiago.happyrobot.dev/?view=reservations&load=LD01088&run=ec839a6a-d47f-49a7-94d7-617c19049b7f) for its $975 opening, $1,000 agreement, native recording and Twin timeline. [Bookings](https://carrier-sales-santiago.happyrobot.dev/?view=bookings&load=LD01080&run=ddae86e8-c7b0-43b6-8dc1-eb902b45c33f) contains the separate historical PENDING acknowledgement. [Overview](https://carrier-sales-santiago.happyrobot.dev/?view=overview) explains 49 recorded calls, the conversion to a reservation, losses and carrier payment changes.

Updated 2026-11-04 (Australia/Sydney). The shared starting map for the owner, Claude Code and Codex. A Git clone includes everything tracked here. It does not include browser sessions, local `.env`, ignored evidence or MCP authentication.

## Read first

1. [`../AGENTS.md`](../AGENTS.md): who writes, how work is reviewed, and the writing rule.
2. [`../ARCHITECTURE.md`](../ARCHITECTURE.md): how the system works.
3. [`decisions.md`](decisions.md): why it works that way, and what is still open.
4. [`assignment.md`](assignment.md) and the [assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf): requirements and deliverables.
5. [`questions.md`](questions.md): Luke's November 5 acceptance of the PENDING handling, ZIP submission route, reviewer timing and sandbox inventory limits of evidence.
6. [`tms/README.md`](tms/README.md) and [`tms-contract.md`](tms-contract.md): protocol usage, live observations and spent inventory.

Keep requirements, observed behaviour, assumptions and simulations distinct. The handbook is a field manual with sample transcripts, and a live discrepancy must be recorded with its scope. Reading `PENDING` as any particular business stage is an interpretation, not a confirmed contract.

## Current state

| Area | State |
|---|---|
| `main` | Use the unified carrier-sales workspace and Overview. Build 23 from `147eb49` is the verified performance baseline. Workflow Version 8 and service release 17 power the calls. The owner adds the video URL and submits the ZIP. A GitHub invite applies if the private-link alternative is chosen after reviewer assignment. |
| `prototype/e2e` | Working system at `4b5ef3a`. Reference only. Not merged. See [lessons](lessons-from-prototype.md). |
| `lab/harness-v24` | Earlier Codex test harness, kept locally. Historical. |
| Who does what | One writer at a time on main. Codex handles implementation, validation and a separate read-only review. Claude can provide additional audits when available. The owner approves every push. |
| Spent loads | Listed in [`tms-contract.md`](tms-contract.md#booking-test-inventory) and [`blocked-loads-v1.json`](../service/policy/blocked-loads-v1.json). No supported cancel/reset is established; no quota or permanent-consumption claim follows. |

Workspace: [FDE - Santiago Gonzalez Alvarez](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez), organization ID `01a17a99-0856-7f88-b09f-4b787e20413c`.

| Platform resource | Identity | State |
|---|---|---|
| Real workflow, the target | Inbound Carrier Sales, `01a18119-67a1-79a3-b220-369aa359d4fb`, slug `6oaskq84xpfc` | Version 8 (`kvexhw5fzj4y`, UUID `01a1a4f6-79a3-7c40-8732-589b3adfdcfd`) live since 2026-11-04, replacing Version 7. Prompt SHA-256: `53a884aea629114fa6d3342b9c8cf9f392bf376ca053622ab1f561821d33437c`. |
| Prototype workflow | `01a19476-5384-704b-9c5e-569fd96f9adf`, slug `yhcdrf4kne4j` | Historical owner-call evidence retained; unpublished on 2026-11-04. |
| Operations app | Carrier Sales; existing slug `codex-lab-carrier-sales-v24`, alias `carrier-sales-santiago.happyrobot.dev` | Use the published alias for Reservations, Overview, Bookings, Calls and Demand. Reviewed Build 23 introduced the reconciled voice sample. Booking sends remain off. See [dashboard release](releases/2026-11-04-dashboard-clarity/README.md). |
| Prototype service | Fly app `codex-e2e-lab-sg-20261031`, `iad` | Stopped, bookings off. |
| Prototype Twin tables | `proto_*` | Keep until the build no longer needs them. |
| Build Twin tables | `calls`, `bookings`: `id` text primary key, `version` int, `data` jsonb | Created on 2026-11-02. Schema checked, and version-checked writes proven from Fly on 2026-11-03 (T-1). |

After owner approval, Claude reports pushing `bf512aa`, deploying Fly release 17, then publishing Version 6. Codex independently verified GitHub main, 28 matching deployed runtime source/policy files, the healthy machine, authenticated health/snapshot reads, missing-key 401 on `/calls/ended`, and the exact live prompt. At that earlier release check, the native App selector showed production Build 20; source 48ba398/import 97da4f6 is reported in Claude's release handover, the 77-file archive matches the checkout, and the final visual check passes. See [release verification](releases/2026-11-04-v6/README.md). LIVE_BOOKING remains false and CALL_COHORT remains synthetic. Six test reservations were declined on 2026-11-04. Committing later documentation does not deploy it. The repository privacy/access check from 2026-11-03 found only the owner and zero pending invitations; that was an access snapshot. Luke later accepted a portal ZIP without a prior GitHub invitation.

Historical Version 7 publication matched reviewed 9d7a149. Version 8 subsequently replaced it under the owner's non-portal release approval, with exact post-publication root and tool readbacks matching eaa2661. No service deployment, App publication or secret change was needed. See releases/2026-11-04-v8/README.md. The owner withdrew portal-writing authorization and handles final submission alone. Do not open, fill, upload to or submit through the portal. If the private-link alternative is chosen, Luke can provide the reviewer account after submission. HappyRobot workspace access is separate.

Refresh this before relying on it. Do not edit a published workflow version, or reconstruct editor URLs.

## Setup for the build

One-time setup below is already complete for the existing deployment. Do not recreate tables, keys or apps. Any secret change or deployment needs owner approval.

1. **Twin tables.** In the Twin UI, create `calls` and `bookings`, each with `id` (text, primary key), `version` (int) and `data` (jsonb, not json). The API cannot create tables. Leave the `proto_*` tables alone.
2. **Twin key.** Create an Editor API key for the service. Do not reuse a lab key. Editor applies workspace-wide while tag scopes are off.
3. **Fly app.** Put a payment method on the Fly account, because the trial stops machines after about 5 minutes. The app is `happyrobot-carrier-sales-sg` in `fly.toml`, created with `fly apps create`.
4. **Secrets.** `AGENT_API_KEY`, `OPS_API_KEY`, `OTP_HASH_SECRET` and `PRICING_SECRET` are generated into the ignored `.env`, at least 24 characters each. `make secrets` copies exactly the settings `config.py` reads into Fly secrets without printing them, and `make deploy` deploys. `make run` runs the same image locally.
5. **Gmail.** Create an app password for the demo inbox.

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
| Fly.io | The CLI is installed and authenticated. The service is `happyrobot-carrier-sales-sg` at `https://happyrobot-carrier-sales-sg.fly.dev`, one machine in `iad`. Release 17 from reviewed `bf512aa` is healthy on 2026-11-04, with all 28 runtime source/policy files matching the checkout. |

Local credentials are not part of a clone. Use the owner-managed ignored .env and platform secret settings; do not assume an old prototype worktree is the current source. Secret values and their synchronization were not inspected for this documentation pass. Never copy credential values into documentation, prompts or commits. `.gitignore` prevents commits, not access, so keep raw studies, codes, ceilings and credentials out of runtime voice context.

## FMCSA integration starting point

Official [Quick Start](https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted) and [API reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi). The docket lookup used:

```text
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/<MC_DIGITS>/?webKey=<FMCSA_API_KEY>
```

Never log the full URL, because it contains `webKey`. A returned record or HTTP 200 alone does not establish eligibility. The rule is in [architecture section 8](../ARCHITECTURE.md#8-verification-and-the-one-time-code), and checked carriers are in the [ledger](test-carriers.md).

## Keeping this true

Update this page, the architecture and the decisions log together when real state changes. A local commit is visible only in this checkout until the owner approves a push.
