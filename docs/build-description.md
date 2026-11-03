# Inbound Carrier Sales: build description

For HappyRobot Logistics' business and IT review. This is a proof-of-concept submission candidate. The service and workflow Version 4 are live; the App improvements remain local until approved for publication. The release checklist is in submission.md.

## Customer problem and scope

The brokerage wants to automate repetitive inbound qualification, matching and negotiation while keeping a senior rep responsible for the booking decision. This candidate demonstrates that first leg through HappyRobot web calls, an integration service and a HappyRobot Apps operations screen. It does not establish production capacity, answer-rate improvement, reduced burnout or financial return.

1. **Check authority.** Take an MC number, look it up in FMCSA, confirm the returned carrier name with the caller and distinguish refusal from an unavailable service.
2. **Check the emailed code.** Send a code to the configured demo inbox and check what the caller reads back before discussing loads. This demonstrates the code gate and access to that inbox, not the caller's legal carrier identity.
3. **Find and price loads.** Read available loads matching equipment and state-level lane preferences. Offer a price below the private ceiling, with at most three counter rounds across the call.
4. **Record agreement.** Save one tentative reservation at the agreed rate. The agent speaks a mocked handoff to a senior rep. A reservation is not a final TMS booking.
5. **Rep review.** Show the captured carrier, shipment details, pickup/delivery, posted and agreed payment, negotiation activity and next action. Only the rep's Confirm can submit a booking request. Sends off or unknown mode disables Confirm.

## Rules and boundaries

The voice model requests actions; the service decides from stored state and fresh TMS reads. Authority, code checks, rate bounds, round counts, reservations and rep version checks are service rules. The model never receives the expected code or raw ceiling. Withholding the field prevents direct field exposure; it does not prove that offers reveal no indirect information. The load-specific cap makes exact inversion harder, while known policy bands still constrain possible ceilings.

The TMS has no supported cancellation or idempotency key. A rep's Confirm rechecks the load and ceiling, wins a version-checked state change, then sends once. A timeout or incomplete result is unknown and is never resent. A complete reference-bearing PENDING receipt is an acknowledgement, not final confirmation. No live BOOKED receipt has been observed. No inventory quota or permanent consumption guarantee is inferred from those observations.

## What operations can inspect

Twin stores structured service activity: authority decisions, code delivery outcome, search criteria and returned public pitch details, each heard and normalized carrier ask, response and round, reservation and rep events, closing notes when supplied, and the workflow end report when delivered. State and its event are written together in the same row.

This is sufficient to reconstruct service decisions without raw platform logs; it is not a verbatim recording or proof of what was spoken. Missing notes are shown as missing. End capture depends on the workflow reaching its callback and Twin accepting it. Pre-tool calls become visible after Version 4's callback is deployed and published successfully. No external database or general-purpose logging framework is used.

The App separates real and test calls. Its metrics count recorded calls, reservations, rep approvals, pending acknowledgements, final confirmations, unknown outcomes and unmatched demand. The northstar is recorded reservations per call that ever passed its code. Tool-to-offer time begins at the first service request, excluding greeting and spoken delivery. Complete definitions and missing-data behavior are in kpis.md. Carrier payment and concessions are not brokerage revenue or profit.

## Evidence

The layered package in qa-package.md separates service tests, seeded generated inputs, conversation checkpoints, complete HTTP journeys, native model simulations and human voice calls. Current raw totals, versions, failures and reruns are in qa-results.md; they must accompany any presentation of success.

One earlier real-integration call reached agreement and a rep Confirm whose TMS reply was PENDING. The owner's Version 3 transcript also shows name confirmation before code delivery, unmatched searches, an agreement through negotiate, a mocked handoff and clean close. The Version 4 candidate's E7 continuation passed eight repetitions, with ten additional continuation/regression checkpoints passing. The standard full text simulation reached a truthful handoff; the pressure simulation held verification but ended by idle timeout without closing notes. These small samples do not prove broad reliability. Human voice acceptance of Version 4, interruptions and final published-App visual review remain release checks.

## How it runs and who owns what

| Component | Location | Responsibility |
|---|---|---|
| Voice workflow | HappyRobot | Web-call conversation and six service tools; Version 4 adds the post-agent end report |
| Carrier Sales Service | Python 3.12 Docker container on Fly.io | Rules, FMCSA, code email, raw-TCP TMS adapter, Twin writes and rep actions |
| Twin | HappyRobot | Call and booking rows, each with its own event history |
| Operations App | HappyRobot Apps | Authenticated review, metrics and rep decisions through the service |

After one-time cloud and secret setup, make deploy builds and deploys the container to the approved Fly environment. Voice and operations routes use separate credentials. The App verifies the signed-in user and keeps its service key server-side. No secret value belongs in the repository, prompt, video or submission.

## Tailored next steps

1. Agree pricing assumptions, the MAX_BUY mapping and TMS finalization/cancellation behavior.
2. Replace the shared demo inbox with trusted carrier-contact records and an appropriate identity process.
3. Validate expected capacity and conversation behavior, including speech recognition, interruptions and failures.
4. Run a supervised pilot with agreed success criteria and review of unknown outcomes.
5. Consider real telephony and operational notifications after those checks.
