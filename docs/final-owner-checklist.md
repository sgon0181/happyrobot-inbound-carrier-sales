# Historical baseline finish checklist

This preserves the earlier Version 8 finish plan, including its superseded Real/Test screen instructions and retained-clip recording plan. Do not use it to record the current candidate. Use the [new five-minute owner script](proposal-demo.md), [candidate readiness](readiness.md) and [updated prospect email](proposal-prospect-email.md). The owner still controls the final portal submission; all actions and counts below are dated baseline history.

The reviewed fix is live: workflow Version 8 and service release 17 with the native Carrier Sales App. The owner retains sole control of the submission portal. Do not open, fill, upload to or submit through it. The recorded confirmation regression and verification are in [confirmation-fix.md](confirmation-fix.md). Booking sends stay off and calls stay synthetic. No service redeployment, new booking, BOOKED result, capacity benchmark or cohort change is required to finish this submission.

## 1. Historical Version 7 test script, superseded

Do not use this script as a new required call. The owner ran the next Version 7 calls and found the confirmation defect, now fixed and verified in Version 8. This contrived high-ask script is retained only as history. Availability below is historical, not a current lane recommendation.

Open the [web-call demo](https://platform.happyrobot.ai/deployments/6oaskq84xpfc). Use MC **138328**, confirm the returned carrier name and read the actual emailed code. Never paste it into chat or show it in the video.

The read-only check at 2026-11-04 04:05 UTC found **LD01120**, reefer from **Augusta, Georgia, to Lexington, Kentucky**, OPEN and not locally held. Pickup: **November 11 at 7:18 PM Central (CST)**. Delivery: **November 13 at 9:18 PM Central (CST)**. Expected opening offer: **$975**. Note: **reefer set to 38F continuous**. Availability can change; if the service cannot offer it, Codex supplies a fresh checked lane rather than asking you to improvise.

The initial range deliberately requires clarification. A clear complete number in ordinary words can correctly go directly to negotiate, so do not use a normal 3825 statement to test ambiguity. Wait for the agent's reply between each line:

| When | Say | Expected behavior |
|---|---|---|
| Asked for equipment/lane | "Reefer, from Georgia to Kentucky." | Pitch the actual load, supplied times and 38F continuous setting before the offer question |
| Asked whether the price works | "I need somewhere between thirty-eight hundred and thirty-nine hundred dollars." | Ask for one complete total |
| Asked for the complete total | "Thirty-eight hundred." | Read back 3800 and ask for confirmation; no negotiate yet |
| Asked to confirm 3800 | "Twenty-five dollars." | Ask for the complete total again; do not submit either fragment or infer 3825 |
| Asked again | "Three thousand eight hundred twenty-five dollars." | Read back 3825 and ask for confirmation |
| Asked to confirm 3825 | "Yes." | Submit exactly 3825 to negotiate |
| If it counters | "Yes, that works." | Accept the actual service-approved offer, without another amount-clarification loop |

At agreement, hear the approved load/rate, mocked senior-rep handoff, thanks and goodbye, followed by proactive agent hangup. Codex reviews the exact arguments, timed transcript and Twin close/end records. State whether the whole closing was audible, because recordings were unavailable in the last review.

This call may create a local reservation. It does not submit to the TMS while booking sends are off. Your successful Version 6 refusal, repetition, failed-negotiation and time checks still count. Do not repeat that suite. If this focused check passes, stop tuning and record the walkthrough.

## 2. Record the approximately five-minute walkthrough

Use [the run sheet](walkthrough.md). Show the customer problem, a verified live flow, the App's reservation and timeline, the historical PENDING receipt, distinct QA layers and five practical next steps. The recording may include the focused acceptance call if the result is suitable.

Keep the App on **Test** to show the new synthetic call. Show Confirm disabled. LD01080 in Real Bookings is the earlier PENDING acknowledgement, not a new booking from this demo. Hide the code, keys, private ceiling and credential-bearing portal URL. Record the video and provide its viewing URL.

Explain: the model conducts the conversation, the service enforces eligibility/code/rate/round rules, Twin stores decisions, and the rep owns submission. A reservation and PENDING acknowledgement are separate from final TMS confirmation. Capacity and financial impact remain unproven.

## 3. Owner-controlled submission

- Push reviewed commits and record the verified workflow, service and native App release details.
- Refresh the build-description PDF, prospect summary text, source ZIP and manifest from tracked source only.
- The owner alone enters portal fields, attaches files and submits. Codex leaves the portal untouched.
- Upload the prepared source ZIP through the portal. Luke accepted this route on November 5. For the optional private GitHub link, ask Luke for the assigned reviewer's account after submission. Keep service keys private.

Earlier blanket submission approval was withdrawn. The owner controls final portal work. The owner reports a successful normal Version 8 call, without independent transcript/audio review of that latest call. The video URL remains outstanding. No additional booking or reservation cleanup is necessary.

## Evidence already available

487 service tests, 1650/1650 statements, 406/406 branches, 256/256 business branches, strict types/lint and Radon B or better. Current Version 8 has 59 checkpoints twice, 118/118 native grades and two inspected recording replays with only 1125 submitted after affirmative confirmation. Historical Version 7 had 51 checkpoints twice, 102/102 native grades. The two historical Version 7 mocked traces preserve 3825 and complete operating notes; neither records final spoken closing. Eleven Version 6 human calls show proactive endings and saved close/end records. The Build 22 baseline had 49 frontend tests, a production build/typecheck, three existing lint warnings and zero production dependency vulnerabilities; prior 1280px visual checks show no page-level clipping and disabled Confirm.

[QA](qa-results.md), [voice evidence](voice-tuning.md) and [Current Version 8 release](releases/2026-11-04-v8/README.md) retain all failures, versions and limits.
