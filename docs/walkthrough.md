# Walkthrough outline, approximately five minutes

The walkthrough uses the recorded Version 8 call, service release 17 and the Overview of reconciled demo calls. The prior App Build 22 is documented in the [dashboard release](releases/2026-11-04-dashboard-clarity/README.md).

Audience: the brokerage's business team, with enough evidence for IT review. Use the customer's repetitive call handling, consistent pricing and reviewable deals as the narrative. Harsha's example is inspiration for clarity, not an architecture to copy.

The opening 3:24 covers the problem, the live Version 8 web call, the rep reservation, the recorded negotiation and the pending TMS receipt. Use the new performance Overview for section 7.

| Time | Show | Explain |
|---|---|---|
| 3:24 to 3:48 | Overview of recorded demo calls | Of 49 calls, 36 verified, 29 found freight and 19 reached an agreement. Inspect losses before and after a match. The median agreed rate was $50 above the opening offer. |
| 3:48 to 4:09 | The service pricing rule | The recorded $975 opening and $1,000 agreement show how the service authorizes a rate within the round limit. |
| 4:09 to 4:45 | The saved test and QA results | Describe the misheard price, required confirmation and measured regression. Distinguish mocked text checkpoints from voice calls. |
| 4:45 to 5:00 | The supervised pilot | Compare dispatch time and verified calls reaching agreement against the desk baseline. |

## Demonstration boundaries

A reservation is not a final booking. PENDING is an acknowledgement. If showing LD01080's saved receipt, identify it as the earlier real rep-confirm example, not the result of the current demo call. Do not click Confirm for a new load without the owner's specific booking approval. No unsupported TMS finalization is invented.

Show calls recorded rather than claiming every call is answered. Explain that the code proves access to the configured demo inbox. Withholding the ceiling is a protection, not proof of zero indirect inference. Do not infer production reliability, margin, revenue or profit from the sample.

The native text simulations do not test audio. The human checklist separately covers greeting, misheard MC, interruptions and closing. Capacity remains unproven unless it is actually measured.

## Before recording

Confirm the exact deployed service commit, live workflow version and App build. Check the callback captures an authorized test call. The current App visual check at 1280px is recorded in the dashboard release evidence. Keep CALL_COHORT synthetic and show the Test view for the demo; a real-cohort demo is optional and requires separate approval. Keep booking sends off. Identify synthetic reservations so they cannot be mistaken for customer work; no cleanup or new send is required.

Finish with these exact customer next steps:

1. Agree pricing assumptions and TMS finalization/cancellation behavior.
2. Replace the demo inbox with trusted carrier-contact records.
3. Validate expected capacity and conversation behavior.
4. Run a supervised pilot with agreed success criteria.
5. Consider real telephony and notifications after those checks.
