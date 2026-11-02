# Onboarding

Checked 2026-11-02 (Australia/Sydney). The shared starting map for the owner, Claude Code and Codex. A Git clone includes everything tracked here. It does not include browser sessions, local `.env`, ignored evidence or MCP authentication.

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
| `main` | Skeleton: docs, tooling and policy files. No service code yet. |
| `prototype/e2e` | Working system at `4b5ef3a`. Reference and fallback. Not merged. See [lessons](lessons-from-prototype.md). |
| `lab/harness-v24` | Earlier Codex test harness, kept locally. Historical. |
| Who does what | One writer at a time on `main`, normally Claude Code, with Codex reviewing. The owner approves every push. |
| Spent loads | Listed in [`tms-contract.md`](tms-contract.md#booking-test-inventory) and [`blocked-loads-v1.json`](../service/policy/blocked-loads-v1.json). The TMS has no reset. |

Workspace: [FDE - Santiago Gonzalez Alvarez](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez), organization ID `01a17a99-0856-7f88-b09f-4b787e20413c`.

| Platform resource | Identity | State |
|---|---|---|
| Real workflow, the target | Inbound Carrier Sales, `01a18119-67a1-79a3-b220-369aa359d4fb`, slug `6oaskq84xpfc` | Web call, Prompt and Inbound Voice Agent nodes only. Unpublished at last check. |
| Prototype workflow | `01a19476-5384-704b-9c5e-569fd96f9adf`, slug `yhcdrf4kne4j` | Production v17 passed the owner run. |
| Prototype app | `codex-lab-carrier-sales-v24`, alias `carrier-sales-santiago.happyrobot.dev` | Deployed. Older than the `ops-app/` source on the branch. |
| Prototype service | Fly app `codex-e2e-lab-sg-20261031`, `iad` | Stopped, bookings off. |
| Prototype Twin tables | `proto_*` | Keep until the build no longer needs them. |

Refresh this before relying on it. Do not edit a published workflow version, or reconstruct editor URLs.

## Setup for the build

Owner steps, needed by slice 2. Everything else can be done by the writing agent.

1. **Twin tables.** In the Twin UI, create `calls` and `bookings`, each with `id` (text, primary key), `version` (int) and `data` (json). The API cannot create tables.
2. **Twin key.** Create an Editor API key for the service. Do not reuse a lab key. Editor applies workspace-wide while tag scopes are off.
3. **Fly app.** Create the app and put a payment method on it, because the trial stops machines after about 5 minutes.
4. **Secrets.** Generate `AGENT_API_KEY`, `OPS_API_KEY`, `OTP_HASH_SECRET` and `PRICING_SECRET`, at least 24 characters each. Set them and the provider credentials with `fly secrets set`.
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
| Fly.io | The CLI is installed and authenticated. |

The main `.env` holds only TMS and handbook values. Newer credentials are in the ignored `.env` of Codex's prototype worktree. Never copy credential values into documentation, prompts or commits. `.gitignore` prevents commits, not access, so keep raw studies, codes, ceilings and credentials out of runtime voice context.

## FMCSA integration starting point

Official [Quick Start](https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted) and [API reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi). The docket lookup used:

```text
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/<MC_DIGITS>/?webKey=<FMCSA_API_KEY>
```

Never log the full URL, because it contains `webKey`. A returned record or HTTP 200 alone does not establish eligibility. The rule is in [architecture section 8](../ARCHITECTURE.md#8-verification-and-the-one-time-code), and checked carriers are in the [ledger](test-carriers.md).

## Keeping this true

Update this page, the architecture and the decisions log together when real state changes. A local commit is visible only in this checkout until the owner approves a push.
