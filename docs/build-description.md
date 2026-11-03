# Inbound Carrier Sales: build description

For HappyRobot Logistics' business and IT teams. It covers what the system does, why it can be trusted with money and carrier data, what was measured, and how it runs. [ARCHITECTURE.md](../ARCHITECTURE.md) has the full technical design.

## What it does

Carriers call in to book loads. Today a rep answers each call, checks the carrier by hand, searches the TMS and haggles. This build answers those calls with a voice agent and hands the rep only the deals worth confirming.

1. **Verify the carrier.** The agent takes the MC number. The system checks the carrier's operating authority with FMCSA, then emails a six-digit code that the caller reads back. No load is discussed before both pass.
2. **Find loads.** The caller names their equipment and lane. The system searches the TMS for open loads with a future pickup and pitches the best match.
3. **Negotiate.** The system prices every offer from the load's private ceiling, with at most three counter rounds per call. The agent never learns the ceiling, so it cannot reveal it.
4. **Reserve.** On agreement the load is reserved for that carrier at that rate, and the agent says it is transferring the caller to a senior rep (the transfer is mocked, as the brief asks).
5. **Confirm.** A senior rep reviews the reservation in the operations dashboard and clicks Confirm. Only then is the booking sent to the TMS, exactly once.

Every call is recorded in Twin, with its outcome, rounds, agreed rate, summary and a step-by-step audit trail.

## Why it can be trusted

Two rules shape the design:

- **The model talks; the service decides.** The voice model can only ask. A separate service checks every request against its own records: whether the carrier passed verification, which loads are open, what rate is allowed. A carrier who talks the model into something still meets the service's rules.
- **Only a rep can send a booking.** The TMS has no cancel. So an agreement on the call only creates a reservation, and a person confirms it. A misheard rate or a confused caller reaches a rep, not the TMS.

What this guarantees, tested on every change:

| Guarantee | How |
|---|---|
| No rate above the ceiling | The service prices and checks every number, and rechecks the ceiling at Confirm |
| The ceiling is never disclosed | It never leaves the service; the agent sees only our offer |
| No loads without verification | The service refuses a search until the call itself shows both checks passed |
| At most three counters | Counted by the service across every load on the call |
| A booking is never sent twice | Confirm must win a versioned write first; an unclear result is held for review and never resent |
| Every action is audited | Each change and its audit entry are saved in the same write |

## Results

Measured on 2026-11-03; details in [QA results](qa-results.md).

- **A real call, end to end.** An active carrier passed FMCSA and the emailed code, found a dry van out of Kentucky, countered twice and agreed at 575 in the third round. The agent spoke the handoff and ended the call. A rep then confirmed it in the dashboard, and the TMS returned a booking reference.
- **Conversation tests.** 19 scripted cases (standard, edge and adversarial) run in HappyRobot with every tool mocked. The live prompt passes 16. All three failures were the same weakness: on an acceptance the agent could close the call without asking the service. The service still held: no reservation, no booking. A two-line prompt fix passes 17 of the 19 every time and the other two most of the time. It awaits review before going live.
- **Service tests.** 411 automated tests with complete statement and branch coverage, including a fake TMS that injects timeouts, partial and malformed replies.
- **Security.** Every endpoint needs a key, each key opens only its own endpoints, and there are no public API docs.

## The dashboard

The operations app in HappyRobot Apps shows, for real calls only:

- **KPIs:** calls answered, code-passed calls, reserved handoffs, the northstar (reserved handoffs per code-passed call), rep-confirmed, TMS-acknowledged and TMS-confirmed bookings, outcomes, and time to first offer.
- **Rep queue:** reservations awaiting a decision, with Confirm and Decline, then sent bookings with their actual TMS status and reference.
- **Call log:** each call's outcome, rounds, summary and audit trail.
- **Turned-away demand:** lanes carriers asked for when nothing matched, which is freight the brokerage is not covering today.

Test calls are kept out of every KPI and shown separately.

## How it runs

| Part | Runs on | Does |
|---|---|---|
| Voice workflow | HappyRobot | Web call, voice agent, prompt and six tools |
| Carrier Sales Service | One Docker container on Fly.io | Every rule: verification, search, pricing, negotiation, reservation, Confirm |
| Twin | HappyRobot | The record of every call and booking |
| Operations app | HappyRobot Apps | Dashboard and rep actions, reading through the service |

- **Integrations:** FMCSA's carrier API, the legacy TMS over its TCP protocol, and Gmail for the codes. TMS reads retry within 6 seconds; a booking is never retried.
- **Deployment:** `make deploy` builds the image and deploys it. Any host that runs a container can run it.
- **Security:** two keys, one for the voice agent and one for the dashboard, compared in constant time. Secrets live in Fly and HappyRobot, never in the code. The dashboard checks the signed-in user and keeps its key on its server.
- **Safety switch:** `LIVE_BOOKING` must be on for Confirm to reach the TMS. It is off by default, because every booking spends a load for good.

## Assumptions to review

The brief left these open, and the brokerage would own the final answer. Each is recorded in [decisions](decisions.md).

- **Booking at Confirm, not on the call (D-22).** The brief has a rep confirm, and the TMS has no cancel, so the booking is sent at the rep's click.
- **`MAX_BUY` is the ceiling (D-10).** The TMS field `MAX_BUY` is used as `max_rate`. A load without a usable one is never offered.
- **`PENDING` is not confirmed.** Every live booking so far returned `PENDING` with a reference, never the handbook's `BOOKED`. The dashboard shows the TMS's own status and never counts `PENDING` as confirmed.
- **Codes go to one demo inbox (D-12).** As agreed for the demo. In production they would go to the carrier's contact on file.
- **Pricing policy (D-4).** Offers usually open 5% under the posted rate and rise in three steps to a cap kept 2 to 6% under the ceiling, varying by load so the ceiling cannot be worked out. The percentages are demo choices for the brokerage to set.

## What is next

- Review and publish the prompt fix, then rerun the evals and a real call.
- Measure capacity: 12 calls of about 4 minutes in parallel, against Twin's 4 statements a second.
- Ask the TMS owner how `PENDING` bookings become `BOOKED`.
