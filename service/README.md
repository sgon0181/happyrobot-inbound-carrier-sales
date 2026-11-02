# Carrier Sales Service

The Python service that decides what the voice agent may do. Slice 1 is built: money, load types, pricing, negotiation, load selection and the read-only TMS adapter, all tested offline. The rest arrives through the [build plan](../ARCHITECTURE.md#15-build-plan) in small commits, each read by the owner.

## Layout

| Path | Job | Rule | Status |
|---|---|---|---|
| `main.py` | Builds dependencies and the app | The only place that connects the parts | Slice 2 |
| `config.py` | Typed settings, validated at startup | The only code that reads the environment | Slice 2 |
| `api.py` | Routes, keys, request models | No business rules | Slice 2 |
| `calls.py` | Voice flows | Calls `core` and `adapters`; no SQL or sockets | Slices 2 and 3 |
| `bookings.py` | Reservation and rep actions | The only code that can reach `LOAD_BOOK` | Slices 3 and 4 |
| `dashboard.py` | Snapshot and KPIs | Read only | Slice 4 |
| `core/` | Pricing, negotiation, money, load selection, carrier policy | Pure functions: no network, files, clock or environment | Built, except `carrier_policy.py` in slice 2 |
| `adapters/` | Twin, TMS, FMCSA, email | Talks to outside systems, holds no business rules | TMS built; Twin, FMCSA and email in slice 2 |
| `policy/` | Versioned pricing policy and blocked loads | Data, loaded once at startup | Built |
| `tests/` | Tests, the fake TMS, the network guard | Test doubles live here, never in production folders | Built |

Dependencies point one way: `api` to `calls`, `bookings` and `dashboard`, then to `core` and `adapters`. `core` imports nothing from the others.

Every commit reports its production line count. Size is watched, not capped ([D-28](../docs/decisions.md)).
