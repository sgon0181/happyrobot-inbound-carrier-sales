# Inbound Carrier Sales

Current dashboard release: **App Build 22**, reviewed source `8ff094a` (clarity change `7262be4` plus explicit empty-field labels). Workflow Version 8 and service release 17 are unchanged. The 80-file source import, 49 frontend tests, checks and live visual review are in [dashboard release](docs/releases/2026-11-04-dashboard-clarity/README.md). Earlier App build/source descriptions below are historical. No voice retest, cohort change or new booking is required.

Current confirmation follow-up: the owner's Version 7 recording exposed a bypass after an explicit No. The narrow Version 8 fix is now live and passes 24/24 focused checks, 118/118 full-suite checkpoints and both mocked recording replays. Pricing is unchanged. See [the correction and its limits](docs/confirmation-fix.md). The Version 7 acceptance wording below is historical and is superseded by this finding.

A voice agent for HappyRobot Logistics, a freight brokerage. Carriers call in, get verified, hear matching loads and negotiate a rate. A senior rep then confirms the booking from an operations dashboard, with no dispatcher involved in the first leg of the call.

This is a proof of concept for the [HappyRobot FDE technical challenge](docs/FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf).

## Status

**Released proof of concept; owner acceptance and submission pending.** Workflow Version 8 (`kvexhw5fzj4y`), Fly release 17 from `bf512aa`, and Carrier Sales App Build 22 are live as of 2026-11-04 Sydney. Booking sends remain off and the call cohort remains synthetic. The App includes structured activity, rep review, send-mode controls and receipt recovery. See [compliance](docs/compliance.md), [QA](docs/qa-results.md) and the [release checklist](docs/submission.md).

An earlier real web call on 2026-11-03 passed authority and code, negotiated and reserved LD01080 at 575. The owner's rep Confirm sent one LOAD_BOOK and stored a reference-bearing PENDING reply as ACK_PENDING. That is evidence of acknowledgement, not final confirmation or broad reliability. Booking sends are currently off; new calls are synthetic until the owner approves changing the cohort.

The owner's ten Version 5 test calls exposed incorrect rate interpretation, premature final-offer wording, repeated offers and closing problems. Service release 17 and historical Version 6 introduced the reviewed fixes. [Voice tuning](docs/voice-tuning.md) now records 11 Version 6 human calls with proactive endings and persisted close/end records. Version 7 addressed split amounts and operating notes, but the next owner call exposed a confirmation bypass. Version 8 fixes that bypass using the actual recording, 118/118 checkpoints and two mocked conversation replays. The owner reports a successful normal Version 8 call; no independent transcript/audio review of that latest call is claimed. Audio recognition and physical timing are not proven by mocked tests. [Current release verification](docs/releases/2026-11-04-v8/README.md) records the live confirmation fix; the [prior release](docs/releases/2026-11-04-v7/README.md) retains App Build 20 provenance and visual checks. Follow [the short finish checklist](docs/final-owner-checklist.md) for the remaining voice, video and submission steps.

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
