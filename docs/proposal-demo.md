# Carrier sales recording cues

This rehearsal uses the known Version 8 recording. The Version 9 and Version 10 candidates remain experimental. Use the filmed workflow until the latest candidate completes its documented voice acceptance gates.

Private rehearsal. The guide voice outside the genuine Version 8 call is synthetic. Record those sections in your own voice before presenting the demo. The redacted call is included as its own editable clip.

The timer follows the rendered rehearsal. Start with a clean tab bar, disable notifications and close the inbox. Open the historical sample and the disposable local simulator in separately labeled tabs. Each is labeled in the video. Use the actual receipt returned during a fresh demonstration.

## 00:00 to 00:14  Client problem

**Show**  Opening title. Let the three operating decisions appear in frame.

**Say**  A carrier with a truck wants to know two things. Is there freight on my lane, and what will you pay? Your dispatchers need to answer quickly, protect the rate and leave the next rep enough information to finish the deal.

## 00:14 to 00:31  Decision ownership

**Show**  Show HappyRobot, the service and the rep. Keep the call and rep decision distinct.

**Say**  HappyRobot takes the call. A service checks motor carrier authority, verifies an emailed code and reads your TMS. The service controls pricing, and Twin records the decisions. The senior rep decides whether to submit the booking. Here is one recorded web call.

## 00:31 to 01:48  Original call

**Show**  Play the sanitized original Werner web call. The caller and agent are both the original audio.

**Say**  Play the original call with the verification code removed. Do not talk over the caller.

## 01:48 to 02:01  The originating reservation

**Show**  Open the Werner reservation for LD01088 and point to its original recording link.

**Say**  That was Werner asking for a reefer from Baton Rouge to Nashville. Here is the same call on the rep's desk. The opening was $975. Werner asked for $1,000, and the service accepted it.

## 02:01 to 02:07  Audit trail

**Show**  Open the originating call timeline, keeping the trial source visible.

**Say**  The rep can listen to the original call or inspect the sequence of decisions before sending anything.

## 02:07 to 02:20  Pricing rule

**Show**  Show the service-owned ceiling and three-round rule, keeping the private value off screen.

**Say**  Why accept the first ask? It fit the service's permitted price for that round. The voice model never receives the private ceiling. Repeating a number buys no extra round, and the third counter is final.

## 02:20 to 02:33  A genuine counteroffer

**Show**  Show the separate recorded LD01127 call timeline, with both carrier asks and the counter visible.

**Say**  Here's a different call. The carrier asked for three thousand. The service countered at $2,825, and both sides settled at $2,750. A supervisor can trace every dollar.

## 02:33 to 02:45  Approve a disposable reservation

**Show**  Switch to the clearly identified local simulator. Select Confirm on LD09001 and approve the native browser prompt.

**Say**  For the button itself, this is a separate reservation in an isolated simulator. The rep checks the terms, then confirms the load, carrier and price. That authorizes one submission.

## 02:45 to 02:51  Observe the receipt

**Show**  Show the simulator receipt for the same disposable reservation.

**Say**  Here is its pending receipt. The desk preserves the reference and the status that actually came back.

## 02:51 to 03:06  Earlier sandbox receipt

**Show**  Switch back to the historical, separately identified LD01080 receipt.

**Say**  This earlier booking was sent to the real sandbox. Its reference also came back pending. Only a confirmed TMS reply counts as booked. If a send times out, the rep investigates before taking another action.

## 03:06 to 03:20  The business KPI

**Show**  Open Overview, Recorded trial. Keep the verified denominator, reservations and rate movement in frame.

**Say**  What did all that calling produce for the desk? Across forty-nine recorded trials, thirty-six callers passed the email check. Nineteen of those calls produced a reservation a rep could review. That's fifty-three percent.

## 03:20 to 03:33  Rate movement and sample

**Show**  Keep the two recorded-trial KPI cards in view, then move down to the funnel.

**Say**  The median agreement was fifty dollars above the opening offer. Eighteen of the nineteen agreements came from one carrier, so this gives us a workflow baseline. A pilot needs more carriers.

## 03:33 to 03:47  The actionable exception

**Show**  Open Verified without a match. Point to the empty-search and no-search counts, then a lane.

**Say**  Seven verified callers never got a match. Six searches returned empty. One call never reached search. I'd check the lanes and equipment for the six, and listen to the seventh before changing the conversation.

## 03:47 to 04:11  Voice QA and guardrails

**Show**  Show the documented price-correction regression and its scope. Mention normal, edge and adversarial checks.

**Say**  Testing covered normal agreements, expired codes and callers trying to skip verification. One recording caught the agent negotiating after a caller rejected a misheard price. We made it repeat the corrected total and wait for yes. The same cases went from sixteen passes in twenty-four to all twenty-four. The broader suite passed one hundred eighteen mocked text checks.

## 04:11 to 04:35  Controlled concurrency

**Show**  Show the separate loopback concurrency run and the counts. Distinguish this from the recorded calls.

**Say**  Two local exercises tested volume. At the Twin rate limit, fourteen of fifteen simultaneous authority checks timed out. Reducing four statements to two let all fifteen finish. In a separate unpaced run, twelve API journeys and twenty-four competing approvals produced twelve TCP booking writes. The pilot still needs to measure concurrent voice calls.

## 04:35 to 04:53  Pilot decision

**Show**  Close on one staffed shift and the measures to compare with ordinary dispatch.

**Say**  For a Monday pilot, I'd connect trusted carrier contacts and keep a rep on every submission. Then compare a similar staffed shift on missed calls, dispatcher minutes and verified calls that turn into reviewed deals. Let's start with one shift and inspect every uncertain send together.

Measured rehearsal duration: 04:53.

The 49 trials span workflow versions. The separate concurrency experiment uses a local TCP simulator. The filmed Werner agreement, second pricing example, historical TMS receipt and rehearsed local reservation each have their own load.
