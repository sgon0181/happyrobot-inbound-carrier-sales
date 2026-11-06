# Inbound Carrier Sales

An AI voice agent that answers inbound carrier calls for HappyRobot Logistics. It verifies the carrier, finds a matching load, negotiates a rate within the broker's limits and records the agreement. A senior rep then reviews the agreement and decides whether to send the booking to the TMS.

**Try it:** [operations App](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview) · [web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) · [workflow](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/l6zo75s4s4vk) · local copy with `make review` (below)

## How it works

```text
Carrier --web call--> HappyRobot voice agent --tools--> Carrier Sales service --> TMS, FMCSA, email
                                                              |
Senior rep --> Operations App (HappyRobot Apps) <------------+--> Twin (calls, bookings, negotiations)
```

1. **Verify.** The agent says it is an AI and asks for the MC number. The service checks active authority with FMCSA and emails a one-time code that the carrier reads back.
2. **Match.** The service searches the TMS for open loads on the carrier's lane and equipment.
3. **Negotiate.** The service prices every offer below a private ceiling and allows at most three counter rounds.
4. **Reserve.** On agreement the load is reserved in Twin and the agent tells the carrier a senior rep will confirm. The transfer is mocked, as the brief allows.
5. **Confirm.** The rep reviews the call and shipment in the App and clicks Confirm, which sends the booking to the TMS once.

Two rules shape the design:

- **The model talks; the service decides.** The voice model can only ask for actions. The service checks every one against its own records. The model never sees the rate ceiling or the code.
- **Only a rep can send a booking.** The TMS has no cancel, so nothing irreversible happens on the call.

## Requirements and where they are met

| Brief requirement | How | Evidence |
| --- | --- | --- |
| FMCSA authority check | Service calls FMCSA; an outage is reported as an outage, not a failed carrier | [Architecture](ARCHITECTURE.md#rules-the-code-enforces) |
| Code after authority, before load details, no bypass | The service refuses load search until its own record shows a verified code | [Results](docs/results.md) |
| Match by lane and equipment | TMS search over the TCP protocol, with fresh detail reads | [TMS reference](docs/tms/README.md) |
| Never exceed or reveal `max_rate` | The ceiling never leaves the service; offers stay under a working cap below it | [Decisions](docs/decisions.md#how-do-we-protect-the-rate-ceiling) |
| At most three counters, then close without transfer | Counted by the service across every load on the call | [Negotiation](docs/decisions.md#how-does-negotiation-work) |
| Tentative reservation, rep confirms, mocked handoff | Agreement creates a reservation; Confirm in the App sends the booking | [Decisions](docs/decisions.md#why-does-a-rep-send-the-booking-instead-of-the-agent) |
| Log MC, load, rate, outcome and notes in Twin | Every state change and its event are saved in one write | [Architecture](ARCHITECTURE.md#data) |
| Operations UI in HappyRobot Apps | Reservations, Overview, Bookings, Calls and Demand views | [KPI definitions](docs/reference/kpis.md) |
| Survive TMS timeouts and malformed replies | Timeouts and bad frames become "unavailable" or "unknown"; a booking is never resent | [Architecture](ARCHITECTURE.md#failure-handling) |
| Authentication on every endpoint | Service keys on every route, including health; App sign-in through HappyRobot | [Architecture](ARCHITECTURE.md#security) |
| North Star KPI, scripted, edge and adversarial tests | Defined KPIs, automated suites and voice evaluations, failures kept | [Results](docs/results.md) |
| Docker and single-command deploy | `make deploy` to Fly.io; `make review` runs everything locally | [Release guide](docs/reference/release.md#reproduce-the-application) |
| Web call, no phone number | HappyRobot web-call trigger | [Workflow](happyrobot/README.md) |

## Known limits

- **Demo identity.** The code goes to a demo inbox, as the recruiter asked. It proves inbox access, not carrier identity. A pilot would enroll real carrier contacts first.
- **Booking sends are off in the hosted App.** Confirm is shown with `make review` and an earlier sandbox receipt (LD01080).
- **PENDING is not BOOKED.** The sandbox TMS acknowledges bookings as PENDING; the App shows that honestly and has no way to finalize them.
- **Some loads go to a rep.** Load text that is not on an approved list is held for review instead of read to the caller (8 of 50 open loads in one check).
- **Voice edge case.** If the agent mishears an amount and the carrier keeps correcting it, the agent can end the call instead of asking again. It never accepts the wrong amount.
- **Scale is not proven.** Tests ran controlled bursts of twelve calls and generated callers, not real peak traffic or a range of accents.

## Try it locally

With Docker Compose and Python 3.12:

```bash
make review
```

This starts the App, service, sign-in, email and a TCP stand-in for the TMS on your machine, then opens a reservation. Confirm sends one booking and shows the PENDING receipt. No real credentials are used. `make review-down` removes it.

## Repository

| Read | For |
| --- | --- |
| [docs/build-description.md](docs/build-description.md) | Business and IT description (the brief's deliverable) |
| [docs/decisions.md](docs/decisions.md) | The key design decisions, as questions and answers |
| [docs/results.md](docs/results.md) | KPIs, test results and voice evaluations |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the parts fit, the rules the code enforces |
| [docs/reference/](docs/reference/README.md) | Full detail: architecture, decision log, KPIs, TMS, release and rollback |
| [docs/history/](docs/history/README.md) | Earlier versions, audits and dated evidence |
| [`service/`](service/README.md), [`ops-app/`](ops-app/README.md), [`happyrobot/`](happyrobot/README.md) | Code for the service, the App and the voice workflow |

AI agents should start with [AGENTS.md](AGENTS.md).

## Development

Use Python 3.12: `python3.12 -m venv .venv`, activate it, then `make install`, `make hooks` and `make check`. `make check` runs lint, strict types, tests and coverage gates, and CI runs the same. Settings are listed in `.env.example`; credentials never enter Git.
