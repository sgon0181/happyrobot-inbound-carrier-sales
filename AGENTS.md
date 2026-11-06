# Guide for AI agents

This repository is a take-home submission: an AI voice agent for inbound carrier sales on HappyRobot, a Python service that makes every business decision, and an operations App. Use this file to find things quickly and to check claims against code.

## Read in this order

1. `README.md`: what it does, requirement table, known limits.
2. `ARCHITECTURE.md`: parts, call flow, the invariants (INV-1 to INV-10) and code layout.
3. `docs/decisions.md`: key decisions as questions; each links to `docs/reference/decision-log.md`.
4. `docs/results.md`: the only place test counts and scores are stated.
5. `docs/reference/`: full detail. `docs/history/` and `happyrobot/history/` are dated records of earlier versions; do not treat them as the current state.

The challenge brief is `docs/FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf`, summarized in `docs/reference/assignment.md`. The TMS protocol and observed behavior are in `docs/tms/README.md` and `docs/tms-contract.md`.

## Where to verify a claim

| Claim | Look at |
| --- | --- |
| Rate ceiling never exceeded or exposed | `service/core/pricing.py`, `service/core/negotiation.py`, `service/core/loads.py` (allowlist), `service/tests/test_negotiation*.py` |
| Code required before load details | `service/core/codes.py`, `service/calls.py`, `service/tests/test_verify.py` |
| Three rounds, redial memory | `service/sale_decisions.py`, `service/negotiation_memory.py`, `service/tests/test_reciprocal_memory.py` |
| One booking send, never resent | `service/rep_actions.py`, `service/bookings.py`, `service/tests/test_rep_actions.py`, `service/tests/test_book.py` |
| TMS timeouts and malformed frames | `service/adapters/tms/`, `service/tests/test_protocol.py` |
| Every endpoint authenticated | `service/api.py`, `service/tests/test_verify.py` |
| Rep-only actions in the App | `ops-app/src/lib/rep-access.ts`, `ops-app/src/lib/auth.ts`, `ops-app/tests/` |
| Live prompt and tools | `happyrobot/prompt-v19.md`, `happyrobot/tool-bindings-v19.json` |
| Deployed state and rollback | `docs/reference/release.md`, `docs/evidence/` |

## Commands

```bash
make check        # lint, strict types, tests, coverage gates, docs check (what CI runs)
make review       # whole system locally with fixtures; Confirm sends to a TCP stand-in
make review-down  # remove the local review environment
```

App checks run from `ops-app/`: `npm ci && npm test && npm run lint && npm run build && npm run typecheck`.

## Rules for changing this repository

- Production code is `service/` and `ops-app/src/`. Keep the gates in `docs/reference/architecture.md` section 14 green and report the production line count in each commit message.
- One writer at a time makes one local commit on `main`; another agent reviews it; nothing is pushed or deployed without the owner's approval.
- State each number once, in `docs/results.md`. `tools/check_docs.py` fails the build if test counts or scores appear in other top-level documents.
- Never put credentials in the repository, prompts or commit messages. `.env.example` lists setting names only.
- Do not use long dash characters (U+2014, U+2013) in documents or output; use commas, colons, semicolons or parentheses.
- Branch `prototype/e2e` is historical reference only. Never merge it.
