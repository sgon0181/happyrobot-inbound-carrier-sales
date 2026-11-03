# Onboarding

Updated 2026-11-04 (Australia/Sydney). The shared starting map for the owner, Claude Code and Codex. A Git clone includes everything tracked here. It does not include browser sessions, local `.env`, ignored evidence or MCP authentication.

## Read first

1. [`../AGENTS.md`](../AGENTS.md): who writes, how work is reviewed, and the writing rule.
2. [`../ARCHITECTURE.md`](../ARCHITECTURE.md): how the system works.
3. [`decisions.md`](decisions.md): why it works that way, and what is still open.
4. [`assignment.md`](assignment.md) and the [assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf): requirements and deliverables.
5. [`questions.md`](questions.md): Luke's answers, and the unanswered Q8.
6. [`tms/README.md`](tms/README.md) and [`tms-contract.md`](tms-contract.md): protocol usage, live observations and spent inventory.

Keep requirements, observed behaviour, assumptions and simulations distinct. The handbook is a field manual with sample transcripts, and a live discrepancy must be recorded with its scope. Reading `PENDING` as any particular business stage is an interpretation, not a confirmed contract.

## Current state

| Area | State |
|---|---|
| `main` | Released service and App source at `8b0e483`, pushed after owner approval. Release documentation is reviewed and committed separately; see submission.md for remaining acceptance and access steps. |
| `prototype/e2e` | Working system at `4b5ef3a`. Reference only. Not merged. See [lessons](lessons-from-prototype.md). |
| `lab/harness-v24` | Earlier Codex test harness, kept locally. Historical. |
| Who does what | One writer at a time on main. Codex is writing this candidate; Claude reviews afterward. The owner approves every push. |
| Spent loads | Listed in [`tms-contract.md`](tms-contract.md#booking-test-inventory) and [`blocked-loads-v1.json`](../service/policy/blocked-loads-v1.json). No supported cancel/reset is established; no quota or permanent-consumption claim follows. |

Workspace: [FDE - Santiago Gonzalez Alvarez](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez), organization ID `01a17a99-0856-7f88-b09f-4b787e20413c`.

| Platform resource | Identity | State |
|---|---|---|
| Real workflow, the target | Inbound Carrier Sales, `01a18119-67a1-79a3-b220-369aa359d4fb`, slug `6oaskq84xpfc` | Version 5 (`zad4fuknryd8`, UUID `01a1a34d-6974-734a-8375-e4740d5807cd`) live since 2026-11-04, replacing Version 4. Prompt SHA-256: `db0ae5ad27f4682296471a335e432f747da53727534e4ebc8f9769656da5ecae`. |
| Prototype workflow | `01a19476-5384-704b-9c5e-569fd96f9adf`, slug `yhcdrf4kne4j` | Historical owner-call evidence retained; unpublished on 2026-11-04. |
| Operations app | Carrier Sales; existing slug `codex-lab-carrier-sales-v24`, alias `carrier-sales-santiago.happyrobot.dev` | Production Build 18, exact `ops-app/` source from `8b0e483`, published and visually checked on 2026-11-04. No lab branding in the visible App. |
| Prototype service | Fly app `codex-e2e-lab-sg-20261031`, `iad` | Stopped, bookings off. |
| Prototype Twin tables | `proto_*` | Keep until the build no longer needs them. |
| Build Twin tables | `calls`, `bookings`: `id` text primary key, `version` int, `data` jsonb | Created on 2026-11-02. Schema checked, and version-checked writes proven from Fly on 2026-11-03 (T-1). |

Claude pushed `8b0e483`, published Version 5 and deployed Fly release 16 on 2026-11-04 after owner approval. The machine was healthy, snapshot read succeeded, and `/calls/ended` refused a missing key with 401. Codex then published App Build 18 as Carrier Sales and checked its UI. LIVE_BOOKING remains false and CALL_COHORT remains synthetic. Six test reservations were declined on 2026-11-04. Committing later documentation does not deploy it. The repository privacy/access check from 2026-11-03 found only the owner and zero pending invitations; reviewer access still needs approval and validation.

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
| Fly.io | The CLI is installed and authenticated. The service is `happyrobot-carrier-sales-sg` at `https://happyrobot-carrier-sales-sg.fly.dev`, one machine in `iad`. Release 16 from `8b0e483` was deployed and healthy on 2026-11-04. |

Local credentials are not part of a clone. Use the owner-managed ignored .env and platform secret settings; do not assume an old prototype worktree is the current source. Secret values and their synchronization were not inspected for this documentation pass. Never copy credential values into documentation, prompts or commits. `.gitignore` prevents commits, not access, so keep raw studies, codes, ceilings and credentials out of runtime voice context.

## FMCSA integration starting point

Official [Quick Start](https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted) and [API reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi). The docket lookup used:

```text
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/<MC_DIGITS>/?webKey=<FMCSA_API_KEY>
```

Never log the full URL, because it contains `webKey`. A returned record or HTTP 200 alone does not establish eligibility. The rule is in [architecture section 8](../ARCHITECTURE.md#8-verification-and-the-one-time-code), and checked carriers are in the [ledger](test-carriers.md).

## Keeping this true

Update this page, the architecture and the decisions log together when real state changes. A local commit is visible only in this checkout until the owner approves a push.
