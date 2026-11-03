# Demo video run sheet

About five minutes, for the brokerage's business team. Record the screen with audio. Times are targets.

## Before recording

1. **Pick a load to spend.** A live Confirm spends a load for good. Ask Claude to find one fresh open load on a lane you will ask for, so the call finds it. Avoid LD01080 and everything on the blocked list.
2. **Turn live booking on**, and back off after the video. Claude can run both on your yes.
3. **Open three tabs:** the HappyRobot web call for workflow Inbound Carrier Sales, the dashboard at https://carrier-sales-santiago.happyrobot.dev (signed in), and the demo inbox that receives the codes.
4. **Have your lines ready:** MC 138328, the equipment and states of the chosen load, and one counter about 10% above the first offer.

## The video

| Time | Show | Say |
|---|---|---|
| 0:00 to 0:30 | Dashboard overview | The problem: every inbound carrier call takes a rep's time. This assistant answers them, verifies the carrier, negotiates within your limits, and leaves the rep only the confirmations. |
| 0:30 to 2:30 | The live web call | Give the MC, read back the emailed code (show the inbox), name the lane, counter once, accept. Point out: no load until both checks pass; the agent only quotes the system's numbers; it hands off to a senior rep. |
| 2:30 to 3:30 | Dashboard | Refresh. The call appears with its outcome and audit trail, and the reservation waits in the rep queue. Click Confirm. Show the reference and the TMS status, `PENDING`, and why it is never counted as confirmed. |
| 3:30 to 4:30 | QA results (`docs/qa-results.md`) | 19 scripted conversations, including attempts to get the ceiling, skip the code or force a booking. Show the one weakness found and the fix waiting for review. Then the guardrails: no rate above the ceiling, nothing booked twice. |
| 4:30 to 5:00 | Build description, KPIs | The northstar is reserved handoffs per verified call. Turned-away demand shows lanes you could add. Close with the assumptions for the business to decide, such as when a booking counts as final. |

## After recording

1. Turn live booking off.
2. Ask Claude to record the spent load in the blocked list and the TMS evidence notes.
3. Upload the video and paste its link into the email draft (`docs/prospect-email.md`).
