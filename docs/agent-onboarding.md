# Coding-agent onboarding

Checked 2026-10-31 (Australia/Sydney). This is the shared starting map for Claude Code, Codex and authorized developers. A Git clone includes the tracked context below; it does not inherit browser sessions, local `.env`, ignored evidence or MCP authentication.

## Read first

1. [`../AGENTS.md`](../AGENTS.md): one writer, local commit on `main`, Codex review, owner approval before push; permanent writing rule.
2. [`../PROJECT_GUIDE.md`](../PROJECT_GUIDE.md) and the local assignment PDF: requirements and deliverables.
3. [`../Questions.Md`](../Questions.Md): Luke's actual clarifications, owner interpretations and unanswered Q8. Gmail access is unnecessary for already transcribed decisions; record material new replies here with date/source.
4. [`tms/README.md`](tms/README.md) and [`tms-contract.md`](tms-contract.md): protocol usage, bounded live observations, fixtures and protected inventory.
5. [`../ARCHITECTURE.md`](../ARCHITECTURE.md): current candidate design, not a deployment report. [`../Research.Md`](../Research.Md) gives rationale; `Archive/` proposals are historical.

Keep requirements, observed behavior, candidate decisions and simulations distinct. The handbook is a field manual with sample transcripts; a live discrepancy must be recorded with scope, not silently generalized. The mapping from TMS `PENDING` to the business's tentative stage is an interpretation, not a confirmed reservation/finalization contract.

## Current state

| Area | What a new agent can rely on |
|---|---|
| In Git | Phase 1 of the service in [`service/`](../service/README.md), with offline tests and live booking off by default. Read-only TMS reader, seven offline reader checks, shared guides, blank environment template, sanitized booking replies, historical test inventory, [platform checks](platform-checks.md) and the [test-carrier ledger](test-carriers.md). |
| HappyRobot | Inspected workflow versions below exist externally. No workflow export, prompt snapshot or test definitions are tracked under `happyrobot/` yet. |
| Ignored local work | Read/booking studies and a booking-policy lab live under `secrets/`. The lab records 37 passing tests, but uses SQLite/fake TMS. The tracked contract carries its useful findings and limits; a clone does not need those folders to understand them. An isolated end-to-end harness with 60 offline tests sits in a Codex worktree, outside this repository; [platform checks](platform-checks.md) carry its findings. |
| Who does what | Claude Code maintains `main`. Codex maintains its isolated harness worktree and reviews Claude's commits. Both start from this file. |
| Still unproven | A complete live voice flow, automatic OTP delivery, Twin coordination and clean call ending. See [platform checks](platform-checks.md). |
| Planned implementation | Service endpoints and authentication, `ops-app/`, notification and FMCSA adapters, Twin coordination, Docker/Fly/Makefile artifacts and production QA results are not tracked implementations yet. Architecture commands such as `make deploy` are future targets. |

Verified external snapshot: workspace [FDE - Santiago Gonzalez Alvarez](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez), organization ID `01a17a99-0856-7f88-b09f-4b787e20413c`, slug `fdesantiagogonzalezalvarez`. The workspace currently uses legacy workflow versions, not workflow branches.

| Workflow | ID / slug | Inspected version and scope |
|---|---|---|
| Inbound Carrier Sales | `01a18119-67a1-79a3-b220-369aa359d4fb` / `6oaskq84xpfc` | `ht173aa7sa17`: Web call, Prompt, Inbound Voice Agent; 3 nodes, 2 edges; inspected version not live and not locked. |
| [CODEX LAB ONLY] Read-only carrier flow 20261031 | `01a18ffa-efe8-7602-8591-a719678d81c3` / `on6nwqbja0vr` | `ov4q0zv7lnnj`: 3 nodes, 2 edges; inspected version not live. Experimental, not the main workflow. |

This snapshot does not prove the state of every environment or other deployment. Refresh read-only metadata before editing. Do not reconstruct editor URLs or edit a published version. Use exact tool-returned URLs and the workspace-supported version workflow. Before claiming platform work reproducible, add an approved sanitized export/snapshot and its version/provenance to Git.

## Access without committing secrets

The private candidate portal link is in Luke's original "HappyRobot | FDE Technical Challenge" email. It is a credential-bearing access link, not a repository reference. Obtain it from the owner or authorized mailbox; do not copy it, invitation tokens or portal HTML into Git.

| System | Authorized access and configuration |
|---|---|
| Legacy TMS | Portal supplies host, port and candidate token. If `.env` is absent, create it from blank [`.env.example`](../.env.example); preserve any existing `.env` and privately fill `TMS_HOST`, `TMS_PORT`, `TMS_TOKEN`. The current reader loads that file directly, not exported shell variables. |
| Handbook | [Manual](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/) uses a password form and cookie session. Documentation-only `TMS_DOCS_PASSWORD` is separate from the TMS wire `AUTH` token. A 401 needs ordinary authorized login, not HTTP Basic or guessed credentials. The observed form posts `password` to `/__login`; scripts may load the value privately, never inline it in shell history or print it. |
| HappyRobot/MCP | Each coding client needs its own approved connection. Codex and Claude Code each have their own OAuth login, and neither shares the other's tokens. Claude Code uses the user-scope server `happyrobot-workflows` at `https://mcp.platform.happyrobot.ai/workflows/mcp`, confirmed on 2026-10-31 by live reads. Use the owner's approved client-specific setup, then read `get_connection_info` and the exact workflow/version with `get_workflows`. Discover integration events/config schemas instead of guessing IDs. See [MCP documentation](https://docs.happyrobot.ai/tools/mcp-server). |
| FMCSA | Use the portal-issued key. `FMCSA_API_KEY` is a proposed future service setting, not consumed by the current TMS reader. Do not create a replacement key by default. Direct requests from the local machine returned HTTP 403, while HappyRobot's native HTTP node worked (T-5). See the request starting point below. |
| Twin | Workflow-native nodes use organization access; external REST needs an organization-scoped HappyRobot API key. **Provisioned 2026-10-31:** after earlier `twin instance not available` failures, Codex reports that a real Production SQL query succeeds. External API access, atomic updates and latency remain untested, so confirm them in T-1 before enabling durable coordination. |
| OTP email | Luke approved an email integration to the candidate's configured demo inbox. Establish the notification workflow/credential and demo destination privately; proposed `DEMO_OTP_EMAIL` is not caller input or proof of real carrier identity. The native email action reached the demo inbox, but the normal workflow trigger returned HTTP 502 twice. T-3 still checks the real trigger and expected-code exposure in run details. |
| Fly.io and application keys | The Fly CLI is installed and authenticated. Lab app `codex-e2e-lab-sg-20261031` exists with zero machines and belongs to Codex's test; do not deploy the product to it. Production deployment and service credentials still need provisioning. Proposed names in `.env.example` are design placeholders, not existing runtime support. Never invent values, include live secrets in prompts, or treat a missing credential as permission to bypass a control. |

Newer credentials (`HAPPYROBOT_API_KEY`, `FMCSA_API_KEY` and the demo inbox) are in the ignored `.env` of Codex's isolated worktree. The main `.env` holds only TMS and handbook values. Never copy credential values into documentation, prompts or commits. Chrome microphone permission is enabled for browser web calls.

A local agent may access ignored paths when explicitly authorized, but `.gitignore` is not access control. Keep raw studies, contacts, OTPs, ceilings and credentials out of runtime voice context; use approved backend outputs. No credential values are required to read this onboarding or the fixtures.

## FMCSA integration starting point

Official [Quick Start](https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted) and [API reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi) document HTTPS JSON and query-parameter authentication with `webKey`. The documented docket lookup shape is:

```text
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/<MC_DIGITS>/?webKey=<FMCSA_API_KEY>
```

This is a schema with placeholders, not a tested request from this repo. The reference also lists carrier-by-DOT, authority and out-of-service lookups, and 400/401/404/500/general error cases. Never log the full URL containing `webKey`; redact it from errors and traces. A returned record or HTTP 200 alone does not establish eligibility.

Real responses through a HappyRobot native HTTP node confirmed the fields in [`test-carriers.md`](test-carriers.md), and [architecture section 6.3](../ARCHITECTURE.md#63-verification-and-the-one-time-code) states the rule they support. Check other values against the [field reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/apiElements); unknown values fail closed. Out-of-service and broker-only cases are not in the ledger yet. The handbook-example MC used in TMS probes is inactive at FMCSA.

## Safe first build slice

Run `python3 scripts/test_query_loads.py` and `python3 -m unittest discover -s service/tests -t .` offline. Read [`tms/fixtures/README.md`](tms/fixtures/README.md) for the six sanitized reply examples. `python3 scripts/query_loads.py --help` is offline; actual queries need credentials and print developer-only internal pricing. Never rerun historical booking harnesses to inspect evidence.

Phase 1 already covers typed TMS parsing, explicit `OPEN` filtering, booking-state/domain rules and the durable-storage interface. Preserve `ACK_PENDING`, `UNKNOWN` and `CONFIRMED`, one-shot submission and blocked pending inventory. Keep live writes disabled until the authorized integration path is ready. No new booking probe is needed to begin this slice.

T-1 Twin coordination, T-2 money/finalization/ownership, T-3 notification trigger and log exposure, T-4 trusted call/operation identity, T-5 FMCSA access and T-6 session ending retain explicit checks/fallbacks in the architecture. A simulator's confirmation is not a real TMS command. Fresh-session Claude can use `/context` to verify `CLAUDE.md` and its `@AGENTS.md` import loaded; the deeper guides are linked for task-specific reading.

Update this map, contract evidence and architecture together when real state changes. A local-only commit is visible in this checkout; another clone receives it only after the normal owner-approved push.
