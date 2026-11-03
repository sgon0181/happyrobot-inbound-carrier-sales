# Inbound Carrier Sales

A voice agent for HappyRobot Logistics, a freight brokerage. Carriers call in, get verified, hear matching loads and negotiate a rate. A senior rep then confirms the booking from an operations dashboard, with no dispatcher involved in the first leg of the call.

This is a proof of concept for the [HappyRobot FDE technical challenge](docs/FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf).

## Status

**Slice 3 of 5 in its final check.** Verification passed a real call on 2026-11-03. Search, negotiation, reservation and close are built, tested and deployed, and workflow Version 2 has the selling tools; it goes live once published, and then a real call should end in a reservation. See the [build plan](ARCHITECTURE.md#15-build-plan).

A working prototype that passed a real end-to-end call is kept on branch `prototype/e2e`, as reference.

## How it works

```text
Carrier --> Voice workflow --> Carrier Sales Service --> Legacy TMS, FMCSA, email
                                     ^        |
Senior rep --> Operations app -------+        +--> Twin (calls and bookings)
```

1. **Verify.** The agent takes the MC number. The service checks FMCSA, then emails a code that the carrier reads back.
2. **Match.** The service searches the TMS for open loads on the carrier's lane and equipment.
3. **Negotiate.** The service prices each offer from a private ceiling, with at most three counter rounds.
4. **Reserve.** On agreement the load is reserved in Twin, and the agent speaks a mocked transfer to a senior rep.
5. **Confirm.** The rep clicks Confirm in the operations app, which sends the booking to the TMS.

Two rules shape the design: the model talks and the service decides, and only a rep can send a booking. [ARCHITECTURE.md](ARCHITECTURE.md) explains how it all fits together.

## Repository

| Path | Contents |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the system works. Start here. |
| [docs/decisions.md](docs/decisions.md) | Every decision, its reason and its cost, plus open checks |
| [docs/lessons-from-prototype.md](docs/lessons-from-prototype.md) | What the prototype proved and what carries over |
| [docs/onboarding.md](docs/onboarding.md) | Access, setup steps and current platform state |
| [docs/assignment.md](docs/assignment.md) | Summary of the assignment and platform |
| [docs/questions.md](docs/questions.md) | Questions to Luke and his answers |
| [docs/tms/](docs/tms/README.md), [docs/tms-contract.md](docs/tms-contract.md) | TMS reference and live evidence, including spent loads |
| [docs/platform-checks.md](docs/platform-checks.md), [docs/test-carriers.md](docs/test-carriers.md), [docs/research.md](docs/research.md) | Supporting evidence |
| [docs/audits/](docs/audits/) | The two independent code audits of the prototype |
| [service/](service/README.md) | The Python service |
| [tools/](tools/check_branch_coverage.py) | Build checks: the branch coverage gate that `make check` runs |
| [happyrobot/](happyrobot/README.md) | Voice workflow export, prompt and test suites |
| [ops-app/](ops-app/README.md) | Operations dashboard source |

## Development

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
make install
```

```bash
make check
```

`make check` runs lint, format, strict type checks, tests, a 90% overall coverage floor and a 90% branch coverage gate on the business rules, and it is what CI runs. Secrets never enter this repository; `.env.example` lists the names.
