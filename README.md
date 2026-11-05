# Inbound Carrier Sales

A voice agent for HappyRobot Logistics, a freight brokerage. Carriers call in, get verified, hear matching loads and negotiate a rate. A senior rep then confirms the booking from an operations dashboard, with no dispatcher involved in the first leg of the call.

**Review the candidate:** [Carrier Sales Candidate, Build 10](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview). It is a separate hosted App backed by the isolated proposal service and Twin staging. [The validated Version 15 agreement](https://carrier-sales-proposal-sg.happyrobot.dev/?view=reservations&load=LD01123&run=8eb82ad6-79b8-4c11-94ab-99bd1ce34c9b) opens the actual automated-caller audio, $2,100 agreement and pending-rep record. Booking sends are disabled. Voice Version 15 runs only in workflow Development; the existing production baseline is preserved.

Start with the [readiness evidence and one-command setup](docs/readiness.md), [business and IT build description](docs/build-description.md) and [five-minute owner script](docs/proposal-demo.md). The native candidate's 91 source files match this App tree. The evidence separates actual audio, text checkpoints, fixture pressure and a new human recording.

**Preserved baseline.** The [original hosted reservations](https://carrier-sales-santiago.happyrobot.dev/) belong to the released baseline. The [filmed Werner agreement](https://carrier-sales-santiago.happyrobot.dev/?view=reservations&load=LD01088&run=ec839a6a-d47f-49a7-94d7-617c19049b7f) links its $975 opening, $1,000 agreement and recording. A different web call, [LD01080](https://carrier-sales-santiago.happyrobot.dev/?view=bookings&load=LD01080&run=ddae86e8-c7b0-43b6-8dc1-eb902b45c33f), has the reference-bearing PENDING receipt from the actual sandbox. Luke approved keeping that acknowledgement separate from a final booking.

[Workflow Version 8](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc) is the published voice baseline. Its [recording regression](docs/confirmation-fix.md) documents a real misheard-price defect. The proposal voice candidate and its separate test evidence are identified in the review guide.

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

## Review in one command

With Docker Compose and Python 3.12 installed, run `make review`. It builds the source, waits for readiness and opens a disposable authenticated App with one reservation. Confirm writes once to a local TCP simulator. No customer credentials, real email or cloud booking are used. `make review-down` removes only that local review environment. [Cloud deployment and tested limits](docs/readiness.md) are separate.

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
