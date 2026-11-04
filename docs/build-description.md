# Inbound Carrier Sales: build description

For HappyRobot Logistics' business and IT review. Workflow Version 8 (`kvexhw5fzj4y`), Fly release 17 from `bf512aa`, and Carrier Sales App Build 22 are live. Build 22 used reviewed source `8ff094a`. The App source in this package adds the recorded demo performance Overview described below. Booking sends remain off and calls remain synthetic. This is a proof of concept; reviewer access and the owner-recorded video URL remain owner delivery steps. The owner alone handles the submission portal. See docs/releases/2026-11-04-dashboard-clarity/README.md for release evidence.

## Customer problem and scope

The brokerage wants to automate repetitive inbound qualification, matching and negotiation while keeping a senior rep responsible for the booking decision. This candidate demonstrates that first leg through HappyRobot web calls, an integration service and a HappyRobot Apps operations screen. It does not establish production capacity, answer-rate improvement, reduced burnout or financial return.

1. **Check authority.** Take an MC number, look it up in FMCSA, confirm the returned carrier name with the caller and distinguish refusal from an unavailable service.
2. **Check the emailed code.** Send a code to the configured demo inbox and check what the caller reads back before discussing loads. This demonstrates the code gate and access to that inbox, not the caller's legal carrier identity.
3. **Find and price loads.** Read available loads matching equipment and state-level lane preferences. Offer a price within the private ceiling, with at most three counter rounds across the call.
4. **Record agreement.** Save one tentative reservation at the agreed rate. The agent speaks a mocked handoff to a senior rep. A reservation is not a final TMS booking.
5. **Rep review.** Show the captured carrier, shipment details, pickup/delivery, posted and agreed payment, negotiation activity and next action. Only the rep's Confirm can submit a booking request. Sends off or unknown mode disables Confirm.

## Rules and boundaries

The voice model requests actions; the service decides from stored state and fresh TMS reads. Authority, code checks, rate bounds, round counts, reservations and rep version checks are service rules. The model never receives the expected code or raw ceiling. Withholding the field prevents direct field exposure; it does not prove that offers reveal no indirect information. The load-specific cap makes exact inversion harder, while known policy bands still constrain possible ceilings.

The TMS has no supported cancellation or idempotency key. A rep's Confirm rechecks the load and ceiling, wins a version-checked state change, then sends once. A timeout or incomplete result is unknown and is never resent. A complete reference-bearing PENDING receipt is an acknowledgement, not final confirmation. No live BOOKED receipt has been observed. No inventory quota or permanent consumption guarantee is inferred from those observations.

## What operations can inspect

Twin stores structured service activity: authority decisions, code delivery outcome, search criteria and returned public pitch details, each heard and normalized carrier ask, response and round, reservation and rep events, closing notes when supplied, and the workflow end report when delivered. State and its event are written together in the same row.

This is sufficient to reconstruct service decisions without raw platform logs; it is not a verbatim recording or proof of what was spoken. Missing notes are shown as missing. End capture depends on the workflow reaching its callback and Twin accepting it. The deployed end-report route and live Version 8 callback can record pre-tool calls when the callback is delivered; delivery is not guaranteed. No external database or general-purpose logging framework is used.

The dashboard uses 49 recorded inbound demo calls across workflow versions. Of 36 calls that passed email verification, 29 found a matching load and 19 produced a reservation for a rep to review. Seven verified calls stopped before a match and ten matched without an agreement. The median agreed payment was $50 above the first offer on the same load, measured on all 19 agreements. The Overview links these figures to individual calls. Desk activity separates the real and test queues for current rep work. See kpis.md for definitions and source coverage.

## Evidence

The layered package in qa-package.md separates service tests, seeded generated inputs, conversation checkpoints, complete HTTP journeys, native model simulations and human voice calls. Current raw totals, versions, failures and reruns are in qa-results.md; they must accompany any presentation of success.

Service release 17 passes 487 offline tests with actual 100% coverage of 1650 statements and 406 branches. The live Version 8 prompt passes 59 locked text checkpoints twice, 118/118 native model grades. An eight-case recording-derived suite scored 16/24 on unchanged Version 7, exposing eight failed executions before the fix. Two complete mocked Version 8 conversations then submitted exactly 1125 only after a corrected readback and explicit affirmative. All external actions were locked. These results test model responses and tool order, not speech recognition or physical voice timing.

Eleven reviewed Version 6 timed call traces show proactive closing and persisted close/end activity. A later Version 7 call exposed a confirmation bypass; Version 8 makes pending confirmation take priority over direct submission. The owner subsequently reported a successful normal Version 8 call. This latest success is an owner report, not an independent transcript or audio review. Earlier failed runs and reruns remain documented. The text replays lack a recorded spoken farewell, so no complete voice-closing pass is inferred from them.

An earlier real-integration call and rep Confirm produced a reference-bearing PENDING reply, which remains an acknowledgement rather than a final booking. Production App Build 22 has a verified 80-file source import, 49 passing frontend tests and sends-off visual evidence; earlier App builds remain historical. The owner video URL and reviewer access remain to be finalized.

## How it runs and who owns what

| Component | Location | Responsibility |
|---|---|---|
| Voice workflow | HappyRobot | Version 8 web-call conversation, six service tools and the post-agent end report |
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
