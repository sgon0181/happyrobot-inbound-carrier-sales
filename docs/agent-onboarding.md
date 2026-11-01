# Coding-agent onboarding

Current candidate work is isolated on prototype/e2e in the e2e-prototype worktree.
Start with [PROTOTYPE_REPORT.md](../PROTOTYPE_REPORT.md) and
[qa-results.md](qa-results.md) for actual deployment and test results.
ARCHITECTURE.md records the candidate design; it is not a deployment report.
The owner authorized this branch's commits and deployment only. Main, the real
workflow, ARCHITECTURE.md and Questions.Md were not changed in this run.

## Source order and workflow

1. Read AGENTS.md and the owner's current instructions. The owner is the sole
   authority for exceptions. One writer changes files; Claude reviews after this run.
2. Read PROJECT_GUIDE.md and the local assignment PDF for requirements.
3. Read Questions.Md for actual clarifications, assumptions and Q8 awaiting Luke.
   Review that answer before final submission. No email is authorized by onboarding.
4. Read docs/tms/README.md and docs/tms-contract.md before any TMS operation.
5. Read ARCHITECTURE.md, the candidate report and the sanitized evidence together.
   Keep requirements, assumptions, observed behavior and simulations distinct.

Do not push, open a PR or edit the original workflow without owner authorization.
The protected workflow ID is 01a18119-67a1-79a3-b220-369aa359d4fb.
The prototype workflow ID is 01a19476-5384-704b-9c5e-569fd96f9adf,
slug yhcdrf4kne4j. Its exact current snapshot is tracked under happyrobot/.
Fork before editing published versions and replace an explicitly named version
when publishing. Do not force. This workspace uses legacy versions; stop if the
API reports a move or retirement rather than trying another writer.

## Implemented candidate

The service contains authenticated endpoints, FMCSA and Gmail SMTP adapters,
strict TCP TMS parsing, service-owned pricing, native-speech consent, per-entity
Twin storage and primary-key claims. Nine existing proto_ tables are reused.
Calls/bookings/OTP rows are authoritative. The legacy aggregate is frozen and
excluded from views. [Storage cutover](storage-cutover.md) records backup,
contention, timing and crash-safety limitations.

BOOKING_MODE defaults to off. Rehearse checks actual voice consent without an
intent or send. Live requires a verified real call and current consented agreement.
A mode flag is not allocation or authorization. Never replay a booking.
The tracked blocked-load policy separates spent, protected and void inventory.
Every historical intent stays blocked. LD01094 also stays blocked from Confirm.

The App is the existing codex-lab-carrier-sales-v24, now named HappyRobot Logistics
Carrier Sales, at https://carrier-sales-santiago.happyrobot.dev. The original
URL remains active. Verified sign-in and server-side ops API access provide T-7's
fallback for the native Twin gateway failure. Rep approval never changes the
external TMS to BOOKED. The candidate App UI source is mirrored in ops-app/;
its newer sandbox commit is not a claim of a Production source deployment.

## Access and setup

A clone does not inherit .env, browser sessions, ignored evidence or MCP login.
Use the blank .env.example and provision existing credentials privately. Never
print, commit or place tokens, portal links, codes, ceilings or contacts in prompts.
The portal URL is credential-bearing and must remain private.

| Integration | Existing setup |
| --- | --- |
| TMS | TMS_HOST, TMS_PORT and TMS_TOKEN, raw TCP, backend only. |
| Handbook | Separate TMS_DOCS_PASSWORD and cookie login, not wire authentication. |
| HappyRobot | Approved client-specific MCP login; service API key and HAPPYROBOT_ORG_ID privately configured. No role changes are authorized. |
| FMCSA | Existing FMCSA_API_KEY. Deployed Fly lookups work; a local 403 does not prove the key is invalid. |
| Email | Gmail SMTP sender and app password in private configuration. Only the configured demo inbox is authorized. |
| Service | Separate AGENT_API_KEY and OPS_API_KEY, plus OTP_HASH_SECRET and PRICING_SECRET. PROTOTYPE_WORKFLOW_ID binds native consent to the prototype. |
| Twin | Existing proto_ tables and approved runtime Editor key. This is workspace-wide access, not proven table-scoped access. No capacity or permission changes. |
| Fly | Existing app codex-e2e-lab-sg-20261031, machine 84eee5dbdd0008, iad, one 256 MB VM. No new resources. Total budget USD3; no hard cap. |

## Safe next steps

Use Python 3.12 and make test for offline checks. The test package blocks external
connections. Never import tests into a live process. Read-only TMS diagnostics can
show internal pricing and are developer-only. Do not attach their output to tools.

Use make deploy for the approved Fly app, make warm during active work and
make idle afterwards. Export private receipts before replacement. Verify the
actual deployed booking mode with the authenticated health route. Keep live off
outside an allocated owner call. The report lists every live send and its outcome.

The final owner call is evaluated as one run against exactly nine architecture
section 11 items, with genuine agent counteroffer and natural consent checked
separately. Video preparation now belongs to the owner. Review final runtime
hashes, current QA, Q8, private reviewer access and publication details before
merging or submitting. No external message or repository push is implied.
