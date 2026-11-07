# Five-minute recording script

Record a genuine call on the final tested workflow, then follow that exact run in the App. The owner speaks all narration. The plan allows 150 seconds of call audio and 150 seconds for narration, navigation and pauses. If the call is longer, use a clearly labeled excerpt and retain access to the full recording. Do not call an edited clip continuous.

## Prepare the tabs

1. [Overview](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview).
2. [Production web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) and [Version 20 editor](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w), verified in the [release guide](reference/release.md#current-release-state).
3. [Reservations](https://carrier-sales-proposal-sg.happyrobot.dev/?view=reservations), with the new run selected after the call.
4. [Calls](https://carrier-sales-proposal-sg.happyrobot.dev/?view=calls) and that run's native recording.
5. [Bookings](https://carrier-sales-proposal-sg.happyrobot.dev/?view=bookings).
6. The disposable local App from `make review`, if demonstrating Confirm.
7. [Results](results.md), scrolled to the negotiation scenarios and voice tables.

Hide private credentials, inbox contents and OTP digits. Do not expose private rate limits while screen sharing. Keep the date scope and provenance visible on metrics. Hosted booking sends remain off under the owner's selected email setup.

## 0:00 to 0:20: business problem and responsibilities

**SHOW:** Overview, then the final workflow and its fixed opening disclosure.

**SAY:**

"Carrier desks need to qualify callers, find freight and negotiate while more calls arrive. This workspace brings those conversations and agreements together. HappyRobot handles speech; my service controls verification and prices. A senior rep controls the booking request. Let's follow one call."

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

**SHOW:** Clearly label the disposable local App before clicking Confirm on its fixture reservation. Show its PENDING receipt. Alternatively, show the [historical LD01080 sandbox receipt](https://carrier-sales-santiago.happyrobot.dev/?view=bookings&load=LD01080&run=ddae86e8-c7b0-43b6-8dc1-eb902b45c33f) without representing it as the current call.

**SAY:**

"Hosted sends are off for this demonstration. Here, a separate local example shows the rep's Confirm action and a pending receipt. Only an authoritative booked response counts as confirmed. An uncertain send stays with the rep for investigation and is never blindly retried."

**If showing the historical receipt instead, SAY:**

"Hosted sends are off for this demonstration. This earlier LD01080 sandbox booking shows a real TMS acknowledgement after rep approval. It is a separate transaction from today's call. Pending means acknowledged, not finally booked. Uncertain sends are investigated rather than blindly retried."

## 3:45 to 4:10: make an operating decision

**SHOW:** Overview funnel and one supporting exception group. Keep scope, counts and denominator visible.

**SAY:**

"The headline shows verified calls reaching a reservation for rep review. Each funnel stage opens its evidence. Exceptions distinguish failed verification, no suitable freight and unsuccessful negotiations. Price movement compares agreement with opening, not profit. This helps a supervisor decide where intervention is needed."

## 4:10 to 4:40: show defensible negotiation and QA

**SHOW:** [Results](results.md): the negotiation scenarios table, then the automated tests and voice tables. Do not show an earlier version's score as the current result.

**SAY:**

"The agent moves toward a carrier who moves toward it, never above our private limit, and inflated or rising asks earn nothing. Calling back does not restart the negotiation. The tests cover repeated asks, concurrent calls, price changes and lost responses, and the voice evaluations and real calls are recorded separately, failures included."

## 4:40 to 5:00: close with the rollout decision

**SHOW:** Return to the operating workspace with the same call visible.

**SAY:**

"The next step is a supervised shift with enrolled carrier contacts and named reps. We'd measure time to an offer, reservation conversion and unresolved calls, then decide where to expand. The result is a carrier desk with consistent decisions and a reviewable record behind each agreement."

## Before recording

Confirm the Production web call still opens Version 20 (see the [release guide](reference/release.md#current-release-state)). Use a fresh available load rather than a historical held one. Preserve unsuccessful runs as evidence. Keep the full call and submission source identifiable. The final video and portal upload are owner actions.
