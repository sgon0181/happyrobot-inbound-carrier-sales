# Carrier Sales Service

The Python 3.12 service owns verification, deterministic pricing, shipment-bound consent, reservations, rep-only TMS submission and complete bounded operations snapshots. The submission source is on `main`; the service uses the populated Twin staging workspace with sends disabled. The old source remains at `oldmain`. [Readiness](../docs/readiness.md) records the exact deployed snapshot, later documentation-only changes and accepted evidence; [architecture](../ARCHITECTURE.md) explains the contracts.

## Layout

| Path | Job | Rule |
|---|---|---|
| `main.py` | Builds dependencies and the app | The only place that connects the parts |
| `config.py` | Typed settings, validated at startup | The only code that reads the environment |
| `api.py` | Routes, keys, request models | No business rules |
| `calls.py` | The call row, and the verify and code flows | Calls `core` and `adapters`; no SQL or sockets |
| `call_state.py` | Call transitions, claims and terminal recovery | Version-checked state changes |
| `selling.py` | Search, negotiation and close | Writes call rows through `calls`; no SQL or sockets |
| `sale_decisions.py` | Shipment-bound negotiation and replay | Pure decisions applied within a call-row write |
| `bookings.py` | Reservation: one booking row per load | No TMS calls |
| `rep_actions.py` | A rep's confirm, decline and reconcile | The only code that can reach `LOAD_BOOK` |
| `dashboard.py` | Complete snapshot and legacy diagnostics | Read only; current Overview formulas live in the App |
| `core/` | Pricing, negotiation, money, load selection, carrier policy, one-time codes | Pure functions: no network, files, clock or environment |
| `adapters/` | Twin, TMS, FMCSA, email | External transport and provider contracts |
| `adapters/twin_reads.py` | Fresh point-read batching | Bounded waiters, detached batches, independent cancellation |
| `policy/` | Versioned pricing policy and blocked loads | Data, loaded once at startup |
| `tests/` | Tests, the fake TMS, the network guard | Test doubles live here, never in production folders |

Dependencies point one way: `api` to `calls`, `selling`, `rep_actions` and `dashboard`, then to `core` and `adapters`. `core` imports nothing from the others.

Every commit reports its production line count. Size is watched, not capped ([D-28](../docs/decisions.md)).

## Run and verify

From the repository root, `make check` runs strict types, lint/format, shape and coverage gates. The reciprocal runtime passed 591 service tests with 98.1% of gated business branches covered. Current release acceptance is tracked in readiness. Use `make review` with Docker Compose and Python 3.12 for the complete disposable App and service; `make run` starts only the service with deliberately supplied settings.

Cloud deployment requires an explicit preconfigured target: `make deploy APP=<isolated-fly-app> APP_URL=<native-app-https-url>`. It verifies authenticated service and TMS readiness before opening the App; it does not provision native resources. Contact enrollment, rep assignment, pacing and retention limits are in the [runbook](../docs/readiness.md), not hidden prerequisites or claims of production readiness.
