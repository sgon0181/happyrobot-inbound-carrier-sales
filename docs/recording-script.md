# Five-minute recording script

Record a genuine call on the final tested workflow, then follow that exact run in the App. The owner speaks all narration. The plan allows 150 seconds of call audio and 150 seconds for narration, navigation and pauses. If the call is longer, use a clearly labeled excerpt and retain access to the full recording. Do not call an edited clip continuous.

## Prepare the tabs

1. [Overview](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview).
2. [Production web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) and [Version 20 editor](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w), verified in the [release guide](reference/release.md#current-release-state).
3. [Reservations](https://carrier-sales-proposal-sg.happyrobot.dev/?view=reservations), with the new run selected after the call.
4. [Calls](https://carrier-sales-proposal-sg.happyrobot.dev/?view=calls) and that run's native recording.
5. [Bookings](https://carrier-sales-proposal-sg.happyrobot.dev/?view=bookings).
6. The [current send window](reference/release.md#current-release-state), checked before recording. The same fresh reservation must be eligible for hosted sandbox Confirm.
7. [Results](results.md), scrolled to the negotiation scenarios and voice tables.

Hide private credentials, inbox contents and OTP digits. Do not expose private rate limits while screen sharing. Keep the date scope and provenance visible on metrics. Live carrier booking remains off. Hosted Confirm is limited to the configured demo MC and temporary challenge-sandbox window. It expires at 02:00 AEDT on November 8. If recording later, obtain a new authorized window first.

## 0:00 to 0:20: business problem and responsibilities

**SHOW:** Overview, then the final workflow and its fixed opening disclosure.

**SAY:**

"Carrier desks need to qualify callers, find freight and negotiate while calls keep arriving. HappyRobot handles speech; my service controls verification and prices; a rep approves bookings. I'm playing the carrier, using a demo inbox and the challenge TMS."

## 0:20 to 2:50: genuine call

**SHOW:** The call with both parties audible, starting with the fixed AI disclosure. Do not narrate over it.

**CALLER PLAN:**

Use MC 138328 and a freshly checked available lane. Read the actual emailed code. Give your equipment and lane (origin and destination states). Ask for one complete total above opening. Respond to the actual returned price, then accept a stated offer if it works. Do not quote a pre-scripted agreement or invent a successful outcome. Follow the current negotiation policy, not the earlier three-step ladder. Allow the agent to finish its agreement, review explanation and goodbye.

## 2:50 to 3:20: follow the same agreement

**SHOW:** The new reservation and its matching call. Point to carrier, shipment, opening and agreed price. Briefly open the native recording and timeline.

**SAY:**

"This is the same call and load. The rep can review the shipment, compare the opening and agreed price, and replay the conversation. The timeline records verification and each rate decision. Agreement creates an internal reservation; it does not claim the load is finally booked."

If no agreement occurred, show the actual exception and say: "This call did not reach an agreement. The desk keeps its outcome and supporting conversation so a rep can decide what to do next."

## 3:20 to 3:45: demonstrate the booking boundary

**SHOW:** Stay on the same fresh reservation. Click Confirm once, accept the confirmation and show its actual receipt, load ID and call link. Do not switch to a fixture or previously submitted load. Keep credentials and private details off screen.

**SAY, if PENDING:**

"I am the authorized rep, approving this same agreement. The service rechecks the shipment and rate, then sends once. Here is the challenge TMS reference. Pending means acknowledged, not finally booked. If we send the request but lose the response, it remains unresolved for investigation, with no automatic retry."

**If UNKNOWN:** say, "The request's outcome is uncertain, so we stop here and investigate. This prevents a second booking." Do not click Confirm again or relabel it as success. If another refusal appears, describe that actual reason and retain the run; do not read the PENDING line.

## 3:45 to 4:10: make an operating decision

**SHOW:** Overview funnel and one supporting exception group. Keep scope, counts and denominator visible.

**SAY:**

"The headline shows verified calls reaching a reservation for rep review. Each funnel stage opens its evidence. Exceptions distinguish failed verification, no suitable freight and unsuccessful negotiations. Price movement compares agreement with opening, not profit. This helps a supervisor decide where intervention is needed."

## 4:10 to 4:40: show defensible negotiation and QA

**SHOW:** [Results](results.md): the negotiation scenarios table, then [Version 20 audits](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/audits/zynb7wm66n9w). Keep the actual audit sample and non-applicable checks visible. Do not show an earlier version's score as the current result.

**SAY:**

"The agent moves toward a carrier who moves toward it, never above our private limit, and inflated or rising asks earn nothing. Calling back does not restart the negotiation. Tests cover repeated asks, concurrent calls, changed shipments and lost responses. Native Northstars audit verification, pricing and closure. Text tests and real voice calls are separate evidence, and failures remain visible."

## 4:40 to 5:00: close with the rollout decision

**SHOW:** Return to the operating workspace with the same call visible.

**SAY:**

"The next step is a supervised shift with enrolled carrier contacts and named reps. We'd measure time to an offer, reservation conversion and unresolved calls, then decide where to expand. The result is a carrier desk with consistent decisions and a reviewable record behind each agreement."

## Before recording

Confirm the Production web call still opens Version 20 (see the [release guide](reference/release.md#current-release-state)). Use a fresh available load rather than a historical held or submitted one. LD01142 is already submitted and is acceptance evidence, not a reusable booking. The checked call used MC 138328, refrigerated equipment, Texas to Florida, one counter and acceptance of the returned offer; availability and the next quoted price may differ. Preserve unsuccessful runs as evidence. Keep the full call and submission source identifiable. The final video and portal upload are owner actions.
