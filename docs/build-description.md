# Carrier Sales: build description

For the brokerage's business and IT review.

## The problem

Inbound carrier calls have grown faster than the dispatch team. Calls are missed at peak times, different dispatchers negotiate to different ceilings, FMCSA checks are manual, and there is no structured record of what was offered or agreed. Carrier Sales automates the first conversation so a carrier can call at any time, get verified, hear a matching load and agree a rate, while a senior rep keeps control of the booking.

## What a carrier experiences

1. The agent introduces itself as an AI and asks for the MC number.
2. It confirms the carrier's name from FMCSA, emails a six-digit code and asks the carrier to read it back. No code, no load details.
3. It asks for equipment and lane, then pitches a matching load: route, pickup time, weight, commodity, rate and any operating conditions or fees.
4. The carrier can accept or counter. The agent answers each counter with the service's price, up to three rounds.
5. On agreement, the agent recaps the load and rate and explains that a senior rep will confirm. It never claims the load is booked.

## Commercial control

All prices come from the service, never from the language model. The TMS ceiling stays inside the service; offers stay under a working cap a few percent below it. We move toward a carrier who moves toward us, in steps of at least $25, and inflated or rising asks earn nothing. The same carrier calling back about the same load continues the same negotiation instead of starting over. [How negotiation works](decisions.md#how-does-negotiation-work).

## Rep control

An agreement reserves the load; it does not book it. The rep opens the reservation in the App and sees the carrier, the shipment, the opening and agreed rates, every price decision and a link to the call recording. Confirm rechecks that the shipment has not changed and that the current ceiling still covers the agreed rate, then sends the booking to the TMS once. The App shows the TMS reply as it is: PENDING is acknowledged, `BOOKED` is confirmed, and an unclear result is flagged for the rep and never resent.

## What operations sees

| View | Answers |
| --- | --- |
| Reservations | Which agreements are waiting for a rep, with their calls |
| Overview | How many verified calls end in a reservation (the North Star), and where the others stop |
| Bookings | What the TMS has acknowledged, confirmed or left unclear |
| Calls | Every call with its timeline, outcome, notes and recording |
| Demand | Lanes and equipment carriers asked for that we could not fill |

[KPI definitions and current results](results.md).

## How it is built

| Component | Technology | Responsibility |
| --- | --- | --- |
| Voice workflow | HappyRobot web call and inbound voice agent | Conversation, AI disclosure, six tools that call the service, end-of-call report |
| Carrier Sales service | Python 3.12, FastAPI, Docker on Fly.io | Verification, email, pricing, negotiation, TMS connection over TCP, reservations, rep actions |
| Data | HappyRobot Twin | Calls, bookings and negotiations, each change saved with its audit event |
| Operations App | HappyRobot Apps (Next.js) | Signed-in desk for operations and reps |

The legacy TMS is unreliable by design. The service retries reads within the voice deadline, reports an outage honestly instead of guessing, refuses malformed replies and never resends a booking whose outcome is unclear. [Architecture](../ARCHITECTURE.md).

## Security

- Every service endpoint requires a key, including the health check; there are no public API docs.
- The voice agent never receives the ceiling, the expected code, contact details or raw TMS data.
- Only reps assigned by their HappyRobot identity can confirm or decline; other signed-in users can view.
- The code goes only to a configured address, never to one the caller provides.
- Secrets live in Fly and HappyRobot secret stores, never in the code repository.

## Deployment

The service is one Docker image. `make deploy` deploys it to Fly.io after one-time setup of the app and its secrets, then checks that it is healthy and can reach the TMS. Any container host would work. `make review` runs the whole system on a laptop with stand-ins for the TMS, email and sign-in, so IT can try Confirm without touching real systems.

## Testing

Automated tests cover the business rules, failure handling and permissions; the platform's evaluations test the prompt against scripted, edge-case and adversarial conversations; real web calls test the full path with live FMCSA, email and TMS reads. Results, including failures, are in [results](results.md).

## What this demo does not yet do

- The code goes to a demo inbox, so it proves inbox access, not carrier identity. A pilot would use enrolled carrier contacts.
- Booking sends are off in the hosted App. Confirm is demonstrated locally and with an earlier sandbox receipt.
- The sandbox TMS returns PENDING; how a booking becomes final is not defined in the sandbox.
- Loads with unrecognized note text go to a rep instead of being quoted.
- Load testing used controlled bursts and generated callers, not real peak traffic, accents or background noise.

## Next steps

1. Agree the pricing thresholds and the approved shipment vocabulary with the carrier sales team.
2. Enroll trusted carrier contacts and name the reps who can confirm.
3. Run a supervised shift and compare time to first offer, verified calls reaching a reservation and unresolved requests against a normal shift.
4. Then decide on real telephony, notifications and wider rollout.
