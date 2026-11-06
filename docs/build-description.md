# Carrier Sales: business and IT build description

The brokerage needs to qualify incoming carriers, negotiate consistently and give dispatchers a usable record of each agreement. Carrier Sales automates the first conversation and gives a senior rep control of the final TMS request. One populated workspace contains historical and new calls, reservations, exceptions and booking receipts.

## Carrier journey

The workflow begins with a fixed statement identifying the AI agent, followed by the MC-number question. The service checks operating authority with FMCSA, confirms the carrier name and verifies an emailed code before discussing freight. Lookup unavailability is kept separate from carrier ineligibility. The agent asks only for missing equipment and lane details.

Matching reads the TMS, checks availability and validates shipment terms. The caller hears the lane, price and essential operating conditions. Clarifications and corrections are handled before an amount can become an agreement. On acceptance, the service records the exact load, carrier, price and shipment facts. The agent explains that the agreement awaits senior-rep review. It does not claim a completed transfer or final booking.

## Commercial control

Prices are service decisions, not model guesses. The working cap stays below the private TMS maximum. The opening price and concessions are deterministic and auditable.

A first reachable ask may earn a small concession. Subsequent movement requires the carrier to improve their best prior ask, and our movement is bounded by that improvement. Repetition, increased demands and distant asks do not automatically raise our offer. The verified carrier and load share their negotiation memory across calls and restarts. Three rounds is a limit, not a promise to reach the cap. [Exact policy and adversarial results](negotiation-review.md) explain the demo thresholds and business tradeoff.

A caller may still seek the best available deal. The policy limits the cost of that behavior; it does not claim negotiations are impossible to probe or that these thresholds maximize commercial conversion.

## Rep decisions and business visibility

The rep opens a reservation with its call, event timeline and shipment. Submission checks the rep's identity, record version, completed agreement, trusted verification route, current availability and unchanged shipment facts. Only the rep can authorize a send. Historical imports remain view-only.

Overview follows authority, code delivery, verification, matching and reservation. Every stage opens supporting records. Active calls and ended-call exceptions are distinguished. Bookings separates acknowledgement, final confirmation and uncertain sends. Price movement is agreement minus opening; it is not profit or a claim of savings.

The TMS has no established cancellation operation or idempotency key. Confirm records its intent before one send. Ambiguous transport becomes UNKNOWN and is not blindly resent. PENDING remains acknowledged. Only an authoritative BOOKED response becomes confirmed. Luke accepted that separation.

## Shipment validation tradeoff

[`service/core/approved_freight.py`](../service/core/approved_freight.py) uses an approved list of cities, commodity names and operating-note phrases before text can reach the caller. It blocks untrusted instructions, incomplete clauses and contradictions. In the dated feed check, **8 of 50 historical open loads required rep review** and 42 were usable.

This favors controlled disclosure over broad freight coverage. A real brokerage would need an owned process for extending approved shipment terms. The implementation does not silently discard those eight loads as absent inventory, and this release does not replace the approved list with a looser shape check.

## System responsibilities

| Component | Responsibility |
| --- | --- |
| HappyRobot workflow | Fixed AI disclosure, conversation, tools and end-of-call report |
| Python service on Fly.io | Verification, email, pricing, TCP TMS integration and rep actions |
| HappyRobot Twin | Versioned call, booking and carrier/load negotiation records |
| HappyRobot Apps | Authenticated operating desk, metrics and review actions |

Call and booking writes have their own durable histories. Concessions and changed shared prices are persisted before the call record; if the second write fails, a concession can remain spent without having been heard. This conservative boundary prevents retries from refunding concessions. It is not a cross-table transaction. An unchanged opening acceptance with no prior memory or rounds skips a redundant memory write after a fresh read; [capacity evidence](reciprocal-capacity.md) explains that boundary.

## Evidence and limits

Local validation passed **591 service tests**, **98.1% business-rule branch coverage**, and **65 App tests** plus lint, typecheck and production build. The disposable App completed one TCP simulator booking with receipt FAKE0001 and PENDING. Independent review reproduced defects, prompted repairs and checked the regressions.

Historical Version 15 evidence includes three overlapping actual audio journeys and 71/74 native text checks. Those results belong to that exact version. Version 19 is live with the fixed AI disclosure. Its two raw text sweeps scored 70/74 and 73/74, and ten focused checks passed. A real amount-clarification early close remains documented alongside judge interpretation issues. Its complete diagnostic voice journey and actual deployment are tracked in [readiness](readiness.md).

The code goes to a demo inbox, so it proves inbox access, not carrier identity; a pilot would enroll real carrier contacts first. Booking sends are off in the hosted App. The Confirm path is shown with `make review` and the earlier LD01080 sandbox receipt. Measured experiments do not establish missed-call reduction, profit, production peak capacity or human accent/noise coverage. Trusted contact enrollment, operational ownership and representative workload testing remain responsibilities before a customer rollout.

## History

Version 8 and App Build 24 are retained as rollback references. The earlier source is available as `oldmain` and the local `baseline-v8` tag. All original evidence remains available.
