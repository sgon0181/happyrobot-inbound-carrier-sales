# Carrier Sales Service

The Python service that decides what the voice agent may do. Nothing is built here yet: the [build plan](../ARCHITECTURE.md#15-build-plan) adds it in small commits, each read by the owner.

## Layout

| Path | Job | Rule |
|---|---|---|
| `main.py` | Builds dependencies and the app | The only place that connects the parts |
| `config.py` | Typed settings, validated at startup | The only code that reads the environment |
| `api.py` | Routes, keys, request models | No business rules |
| `calls.py` | Voice flows | Calls `core` and `adapters`; no SQL or sockets |
| `bookings.py` | Reservation and rep actions | The only code that can reach `LOAD_BOOK` |
| `dashboard.py` | Snapshot and KPIs | Read only |
| `core/` | Pricing, negotiation, money, load selection, carrier policy | Pure functions: no network, files, clock or environment |
| `adapters/` | Twin, TMS, FMCSA, email | Talks to outside systems, holds no business rules |
| `policy/` | Versioned pricing policy and blocked loads | Data, loaded once at startup |
| `tests/` | Tests and fakes | Test doubles live here, never in production folders |

Dependencies point one way: `api` to `calls`, `bookings` and `dashboard`, then to `core` and `adapters`. `core` imports nothing from the others.

Production Python stays at or under 1,500 lines ([D-28](../docs/decisions.md)).
