# Finish and submit

The build is released: reviewed source bf512aa, healthy service release 17, live Version 6 and App Build 20. The remaining work is targeted voice acceptance, your video and final access/submission approvals. No new booking, BOOKED status, capacity benchmark or cohort change is required by the assignment.

## 1. Three targeted calls, about 10 minutes

Open the [web-call demo](https://platform.happyrobot.ai/deployments/6oaskq84xpfc). Leave booking sends off and calls synthetic. Use MC 138328 for the eligible examples, following the actual FMCSA result and reading the emailed code yourself. Do not paste a code into chat or show one in the video.

| Call | What to do | What must happen |
|---|---|---|
| A: refusal | Give MC 134652, expected ineligible in the earlier handover | On the actual ineligible result, hear the reason, thanks and goodbye; the agent ends without your farewell, extra turn or idle filler |
| B: agreement | Verify, request an available lane and listen to the pickup time. Say "1600 and 25". After clarification, give one complete total. If needed, explicitly accept the offer the service actually returns | No partial number is submitted before clarification. Hear the correct named Central time. At agreement, hear the service-approved load ID/rate, mocked senior-rep handoff, thanks and goodbye before the agent hangs up |
| C: failed negotiation | Verify and find a load. Give a clear ask above its offer, then repeat exactly the same ask once. Continue with distinct asks above each returned offer until negotiation fails | The unchanged offer is described as unchanged. Only a service final_offer is called final. On negotiation_failed, hear a professional refusal and goodbye, no handoff, then agent hangup |

Identical asks do not use another round. Call C therefore needs distinct later asks. Load availability changes; use what the service actually offers. Earlier held synthetic loads can remain held. Claude's handover suggested flatbed MT to AZ and refrigerated LA to TN as alternatives; try different lanes for calls B and C, because call B may reserve its load. Availability is not guaranteed. Avoid relying on earlier held FL to NY, MA to CA and MI to GA loads. Agreement creates a local reservation, not a TMS booking.

Optional fourth short check: correct an MC and interrupt a pitch, then verify recovery. Earlier Version 5 calls cover useful unchanged behavior, but correction/interruption evidence is limited. These targeted calls do not establish every possible conversation.

Tell Codex when you finish, with approximate times or run IDs. Codex will inspect the transcript, exact tool arguments, complete audio delivery, agent_hung_up and stored close/end activity. You do not need to inspect platform logs yourself. Failures and reruns remain in the report; a failed check gets a focused fix before recording.

## 2. Record the approximately five-minute walkthrough

Use [the run sheet](walkthrough.md). The sequence is: customer problem, one verified live flow, App reservation and timeline, historical pending receipt, separate QA layers, five practical next steps.

Keep the App on **Test** to show your new synthetic call. The **Real calls** KPI cards remain historical and exclude tests. Show Confirm disabled. Use LD01080 in Real Bookings only to illustrate the existing PENDING acknowledgement. Do not send another booking or release a reservation for the video.

Keep the explanation simple: the model conducts the conversation, the service enforces authority/code/rate/round rules, Twin stores the decisions, and the rep owns the irreversible submission. PENDING is an acknowledgement, not a finalized booking. This is a tested proof of concept, not a measured claim of production reliability or financial impact.

## 3. Final submission actions

- Review the refreshed build-description PDF in submission/ready-to-submit/. It is already generated and visually checked.
- Add your video URL to the candidate portal and the submission record. The prospect summary email is drafted in [submission.md](submission.md).
- Approve pushing the local documentation commits. Runtime code is already pushed and deployed; no new deployment is needed for these documentation changes.
- Provide/confirm reviewer GitHub handles and approve invitations. The repository is private; the latest read-only access check found only the owner and zero pending invitations. Reviewers also need working HappyRobot workflow/App access. Do not share service keys.
- Review the portal fields, attach the PDF, provide the private repository URL and optionally the prepared source ZIP if useful or requested, and approve submission. Nothing has been uploaded, sent or submitted automatically.

The portal offers repository URL and code ZIP entry, a walkthrough-video URL and file attachments. The assignment still requires a private repository link and reviewer access; a ZIP does not replace that requirement. Its private credential-bearing portal link stays outside the repository. CALL_COHORT can stay synthetic for the demo. Any later cohort or booking-mode change requires separate approval.

## What has already been checked

487 offline service tests, actual 100% service statement/branch coverage, 256/256 business branches, strict types/lint and Radon B or better. The exact live prompt passed 40 checkpoints twice. Frontend clean-copy checks pass with 39 tests, three existing lint warnings, production build then typecheck, and zero production dependency vulnerabilities. All 77 App archive files match the checkout. Published App views and both detail panels were reviewed at 1280x900 with no page-level horizontal overflow and every visible Confirm disabled.

The [QA report](qa-results.md), [voice evidence](voice-tuning.md) and [release record](releases/2026-11-04-v6/README.md) preserve versions, failures and limits. The remaining voice acceptance is specific to the changed Version 6 behavior; it does not erase your Version 5 testing or require repeating every earlier automated scenario.
