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
| In Git | Read-only TMS reader, seven offline reader checks, shared guides, blank environment template, sanitized booking replies and historical test inventory. |
| HappyRobot | Inspected workflow versions below exist externally. No workflow export, prompt snapshot or test definitions are tracked under `happyrobot/` yet. |
| Ignored local work | Read/booking studies and a booking-policy lab live under `secrets/`. The lab records 37 passing tests, but uses SQLite/fake TMS. The tracked contract carries its useful findings and limits; a clone does not need those folders to understand them. |
| Planned implementation | `service/`, `ops-app/`, notification workflow integration, Twin coordination, Docker/Fly/Makefile artifacts and production QA results are not tracked implementations yet. Architecture commands such as `make deploy` are future targets. |

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
| HappyRobot/MCP | Each coding client needs its own approved connection. Codex currently has OAuth MCP access; that does not configure Claude Code. Use the owner's approved client-specific setup, then read `get_connection_info` and the exact workflow/version with `get_workflows`. Discover integration events/config schemas instead of guessing IDs. See [MCP documentation](https://docs.happyrobot.ai/tools/mcp-server). |
| FMCSA | Use the portal-issued key. `FMCSA_API_KEY` is a proposed future service setting, not consumed by the current TMS reader. Do not create a replacement key by default. See the request starting point below. |
| Twin | Workflow-native nodes use organization access; external REST needs an organization-scoped HappyRobot API key. Confirm Settings > Twin Database status, approved gateway/auth route and T-1 atomicity/latency before enabling durable coordination. No working external connection is established by the lab. |
| OTP email | Luke approved an email integration to the candidate's configured demo inbox. Establish the notification workflow/credential and demo destination privately; proposed `DEMO_OTP_EMAIL` is not caller input or proof of real carrier identity. T-3 still checks expected-code exposure in run details. |
| Fly.io and application keys | Deployment and service credentials still need provisioning. Proposed names in `.env.example` are design placeholders, not existing runtime support. Never invent values, include live secrets in prompts, or treat a missing credential as permission to bypass a control. |

A local agent may access ignored paths when explicitly authorized, but `.gitignore` is not access control. Keep raw studies, contacts, OTPs, ceilings and credentials out of runtime voice context; use approved backend outputs. No credential values are required to read this onboarding or the fixtures.

## FMCSA integration starting point

Official [Quick Start](https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted) and [API reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi) document HTTPS JSON and query-parameter authentication with `webKey`. The documented docket lookup shape is:

```text
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/<MC_DIGITS>/?webKey=<FMCSA_API_KEY>
```

This is a schema with placeholders, not a tested request from this repo. The reference also lists carrier-by-DOT, authority and out-of-service lookups, and 400/401/404/500/general error cases. Never log the full URL containing `webKey`; redact it from errors and traces. A returned record or HTTP 200 alone does not establish eligibility.

Implement the architecture's allowed-to-operate, common/contract authority and not-out-of-service checks after verifying exact current fields/value semantics against the [field reference](https://mobile.fmcsa.dot.gov/QCDevsite/docs/apiElements) and sanitized real responses. Full field documentation was not retrievable during this handoff, so those mappings and live behavior remain unverified. Populate [`test-carriers.md`](test-carriers.md) before claiming positive/negative FMCSA coverage; the handbook-example MC used in TMS probes was not validated.

## Safe first build slice

Run `python3 scripts/test_query_loads.py` offline. Read [`tms/fixtures/README.md`](tms/fixtures/README.md) for the six sanitized reply examples. `python3 scripts/query_loads.py --help` is offline; actual queries need credentials and print developer-only internal pricing. Never rerun historical booking harnesses to inspect evidence.

Start with typed read-only TMS parsing, explicit `OPEN` filtering, booking-state/domain rules and durable-storage interfaces. Preserve `ACK_PENDING`, `UNKNOWN` and `CONFIRMED`, one-shot submission and blocked pending inventory. Keep live writes disabled until the authorized integration path is ready. No new booking probe is needed to begin this slice.

T-1 Twin coordination, T-2 money/finalization/ownership, T-3 notification-log exposure and T-4 trusted call/operation identity retain explicit checks/fallbacks in the architecture. A simulator's confirmation is not a real TMS command. Fresh-session Claude can use `/context` to verify `CLAUDE.md` and its `@AGENTS.md` import loaded; the deeper guides are linked for task-specific reading.

Update this map, contract evidence and architecture together when real state changes. A local-only commit is visible in this checkout; another clone receives it only after the normal owner-approved push.
