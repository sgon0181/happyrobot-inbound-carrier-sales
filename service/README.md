# Carrier Sales Service

The Python service that decides what the voice agent may do. Slices 1 and 2's code are built: the business rules, the read-only TMS adapter, Twin storage, the FMCSA check, the emailed code and the three verify routes, all tested offline. The rest arrives through the [build plan](../ARCHITECTURE.md#15-build-plan) in small commits, each read by the owner.

## Layout

| Path | Job | Rule | Status |
|---|---|---|---|
| `main.py` | Builds dependencies and the app | The only place that connects the parts | Built |
| `config.py` | Typed settings, validated at startup | The only code that reads the environment | Built |
| `api.py` | Routes, keys, request models | No business rules | Built |
| `calls.py` | The call row, and the verify and code flows | Calls `core` and `adapters`; no SQL or sockets | Built |
| `selling.py` | Search, negotiation and close | Writes call rows through `calls`; no SQL or sockets | Built |
| `bookings.py` | Reservation: one booking row per load | No TMS calls | Built |
| `rep_actions.py` | A rep's confirm, decline and reconcile | The only code that can reach `LOAD_BOOK` | Built |
| `dashboard.py` | Snapshot and KPIs | Read only | Built |
| `core/` | Pricing, negotiation, money, load selection, carrier policy, one-time codes | Pure functions: no network, files, clock or environment | Built |
| `adapters/` | Twin, TMS, FMCSA, email | Talks to outside systems, holds no business rules | Built |
| `policy/` | Versioned pricing policy and blocked loads | Data, loaded once at startup | Built |
| `tests/` | Tests, the fake TMS, the network guard | Test doubles live here, never in production folders | Built |

Dependencies point one way: `api` to `calls`, `selling`, `rep_actions` and `dashboard`, then to `core` and `adapters`. `core` imports nothing from the others.

Every commit reports its production line count. Size is watched, not capped ([D-28](../docs/decisions.md)).
