# Inbound Carrier Sales

An AI carrier-sales desk for HappyRobot Logistics. It verifies callers, finds freight, negotiates within approved limits and records an agreement for a senior rep to review. The rep sees the originating call, shipment, prices and decision history in one workspace.

[Open Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview). Start with the [build description](docs/build-description.md), [release status and evidence](docs/readiness.md), and [five-minute recording script](docs/proposal-demo.md). This repository's `main` branch is the submission source.

## How it works

1. The workflow opens with a fixed AI disclosure and asks for the MC number.
2. The service checks FMCSA authority and an emailed verification code before releasing freight details.
3. It matches the caller's equipment and lane against the legacy TMS and checks shipment terms.
4. It negotiates with bounded reciprocal concessions. The same verified carrier and load share their price and round budget across calls.
5. Agreement creates a reservation. A senior rep reviews the call and controls any TMS submission.

The model handles conversation; the service controls verification, money and state changes. A repeated request cannot create a second booking send. PENDING remains an acknowledgement, and only an authoritative BOOKED receipt becomes confirmed.

The code goes to a demo inbox, so it proves inbox access, not carrier identity; a pilot would enroll real carrier contacts first. Booking sends are off in the hosted App. The Confirm path is shown with `make review` and the earlier LD01080 sandbox receipt.

## What the desk shows

Reservations brings agreements and their calls together. Overview shows qualification, matching and reservation conversion with supporting records. Calls provides the event timeline and native recording link. Bookings separates pending, confirmed and uncertain receipts. Demand shows where ended calls lacked suitable freight or never reached a search.

Price movement compares agreement with opening, not profit. Historical calls remain visible with their provenance. [KPI definitions](docs/kpis.md) explain the denominators and limits.

## Review locally

With Docker Compose and Python 3.12 installed:

```bash
make review
```

This opens an authenticated local App with a reservation. Confirm sends once to a TCP simulator and shows its PENDING receipt. It uses no customer credentials or cloud booking. `make review-down` removes the local environment.

The latest local checks passed 591 service tests, 65 App tests, strict types, lint and production build. Business-rule branch coverage is 98.1%. [Readiness](docs/readiness.md) separates those results from live integration, text evaluations and spoken-call evidence, and lists outstanding release checks.

## Repository map

| Read | Purpose |
| --- | --- |
| [Architecture](ARCHITECTURE.md), [decisions](docs/decisions.md) | System boundaries and tradeoffs |
| [Submission](docs/submission.md), [review](docs/proposal-review.md) | Reviewer handoff and independent findings |
| [Onboarding](docs/onboarding.md), [TMS reference](docs/tms/README.md) | Setup and integration contract |
| [Service](service/README.md), [App](ops-app/README.md), [voice](happyrobot/README.md) | Source and component maps |
| [Negotiation results](docs/negotiation-review.md), [QA package](docs/qa-package.md) | Adversarial checks and retained evidence |

## Development

Use Python 3.12, install `requirements-dev.txt`, then run `make hooks` and `make check`. The commit hook checks staged source. `.env.example` lists settings; credentials stay outside Git.

## History

`oldmain` and the local `baseline-v8` tag retain commit `15ce2b6`. Version 8 and App Build 24 remain rollback references. Their evidence is retained; [readiness](docs/readiness.md) records the actual deployment state.
