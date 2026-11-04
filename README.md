# Inbound Carrier Sales

A voice agent for HappyRobot Logistics, a freight brokerage. Carriers call in, get verified, hear matching loads and negotiate a rate. A senior rep then confirms the booking from an operations dashboard, with no dispatcher involved in the first leg of the call.

This is a proof of concept for the [HappyRobot FDE technical challenge](docs/FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf).

## Status

**Released proof of concept; owner acceptance and submission pending.** Workflow Version 7 (`67nko7p112j2`), Fly release 17 from `bf512aa`, and Carrier Sales App Build 20 are live as of 2026-11-04 Sydney. Booking sends remain off and the call cohort remains synthetic. The App includes structured activity, rep review, send-mode controls and receipt recovery. See [compliance](docs/compliance.md), [QA](docs/qa-results.md) and the [release checklist](docs/submission.md).

An earlier real web call on 2026-11-03 passed authority and code, negotiated and reserved LD01080 at 575. The owner's rep Confirm sent one LOAD_BOOK and stored a reference-bearing PENDING reply as ACK_PENDING. That is evidence of acknowledgement, not final confirmation or broad reliability. Booking sends are currently off; new calls are synthetic until the owner approves changing the cohort.

The owner's ten Version 5 test calls exposed incorrect rate interpretation, premature final-offer wording, repeated offers and closing problems. Service release 17 and live Version 6 contain the reviewed fixes. [Voice tuning](docs/voice-tuning.md) now records 11 Version 6 human calls with proactive endings and persisted close/end records. A remaining split-amount failure and omitted operating notes are addressed in live Version 7. The exact reviewed fix is published; one focused voice acceptance call remains. [Release verification](docs/releases/2026-11-04-v7/README.md) records the live service/prompt, App Build 20 provenance and final visual checks. Follow [the short finish checklist](docs/final-owner-checklist.md) for the remaining voice, video and submission steps.

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
| [Diagram collection](docs/diagrams/index.html) | Teaching atlas, caller journey and historical diagrams, with viewers, PDFs and SVGs |
| [docs/decisions.md](docs/decisions.md) | Every decision, its reason and its cost, plus open checks |
| [docs/build-description.md](docs/build-description.md), [docs/qa-package.md](docs/qa-package.md), [docs/qa-results.md](docs/qa-results.md) | Business/IT description, separate QA layers and actual results |
| [docs/submission.md](docs/submission.md), [docs/walkthrough.md](docs/walkthrough.md), [docs/kpis.md](docs/kpis.md) | Submission draft and approvals, five-minute outline and precise KPI definitions |
| [docs/lessons-from-prototype.md](docs/lessons-from-prototype.md) | What the prototype proved and what carries over |
| [docs/onboarding.md](docs/onboarding.md) | Access, setup steps and current platform state |
| [docs/assignment.md](docs/assignment.md) | Summary of the assignment and platform |
| [docs/questions.md](docs/questions.md) | Questions to Luke and his answers |
| [docs/tms/](docs/tms/README.md), [docs/tms-contract.md](docs/tms-contract.md) | TMS reference and live evidence, including spent loads |
| [docs/platform-checks.md](docs/platform-checks.md), [docs/test-carriers.md](docs/test-carriers.md), [docs/research.md](docs/research.md) | Supporting evidence |
| [docs/audits/](docs/audits/) | The two independent code audits of the prototype |
| [service/](service/README.md) | The Python service |
| [tools/](tools/check_branch_coverage.py) | Build checks: the branch coverage gate that `make check` runs |
| [happyrobot/](happyrobot/README.md) | The voice prompt, its tools and the conversation evals |
| [ops-app/](ops-app/README.md) | Operations dashboard source |

## Development

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
make install
make hooks
```

```bash
make check
```

`make check` runs lint, format, strict type checks, tests, a 90% overall coverage floor and a 90% branch coverage gate on the business rules, and it is what CI runs. `make hooks` makes git run it before every commit on exactly the staged files, so a failing commit is refused locally too. Secrets never enter this repository; `.env.example` lists the names.
