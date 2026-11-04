# Walkthrough outline, approximately five minutes

Current dashboard release: **App Build 22**, reviewed source `8ff094a` (clarity change `7262be4` plus explicit empty-field labels). Workflow Version 8 and service release 17 are unchanged. The 80-file source import, 49 frontend tests, checks and live visual review are in [dashboard release](releases/2026-11-04-dashboard-clarity/README.md). Earlier App build/source descriptions below are historical. No voice retest, cohort change or new booking is required.

Audience: the brokerage's business team, with enough evidence for IT review. Use the customer's repetitive call handling, consistent pricing and reviewable deals as the narrative. Harsha's example is inspiration for clarity, not an architecture to copy.

Record the reviewed release: service 17 from `bf512aa`, live workflow Version 8 and production Carrier Sales App Build 22. App source 8ff094a has an exact 80-file import and recorded visual checks. Use the successful Version 8 call the owner reports as the demo segment; no repeat of the superseded stress-call script is required. Label a recorded live call honestly. Independent transcript/audio review of that latest call is not claimed. Your Version 6 tests do not need repeating. Never display keys, the expected live code, a private ceiling or a credential-bearing URL. The owner records and chooses the final video URL.

| Time | Show | Say accurately |
|---|---|---|
| 0:00 to 0:25 | The problem and system overview | This PoC automates qualification, matching and negotiation; the rep owns booking submission |
| 0:25 to 2:30 | A HappyRobot web call | MC/name confirmation, authority, authorized emailed code, lane/equipment, an explicit counter or acceptance through negotiate, mocked handoff and clean close |
| 2:30 to 3:30 | The operations App | Carrier, lane, schedule, posted/agreed payment, asks and responses, notes, send mode and next action. Missing historical details say Not recorded |
| 3:30 to 4:15 | QA package and results | Actual service count/coverage, seeds, checkpoint repetitions, complete simulations and human calls as separate layers. Show retained failures and the E7 follow-up |
| 4:15 to 5:00 | Five next steps | Agree pricing/TMS contract; trusted contacts; capacity/conversation validation; supervised pilot; then telephony/notifications |

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
