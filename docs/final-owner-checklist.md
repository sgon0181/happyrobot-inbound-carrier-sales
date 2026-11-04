# Finish and submit

The service and App are released: healthy service release 17, live Version 6 and App Build 20. Your 11 Version 6 calls now establish proactive endings in timed traces and saved end records. One wrong-amount reservation and one omitted-note pitch led to the approved Version 7 fix. That draft is tested but unpublished. Review and approve its publication before the two focused voice checks below. No service deployment is needed. Booking sends stay off and calls stay synthetic.

## 1. Two focused calls after approved Version 7 publication

Codex should first read current load availability and give you exact lane/load details. Do not reuse a held lane blindly: LD01116, LD01112, LD01100 and LD01102 are held from the latest tests. No hold was released. Use MC 138328 if FMCSA still returns eligible, confirm the carrier name and read the emailed code yourself. Never paste a code into chat or show one in the video.

| Call | What to do | What must happen |
|---|---|---|
| A: trailing fragment | On a supplied available load, say "3800 and 25". When asked for a complete total, say only "3800". At the 3800 readback, say "25 dollars". When asked again, say "Three thousand eight hundred twenty-five dollars". At the 3825 readback, first correct it to another complete total to check a fresh readback. Then confirm yes only if you want that ask submitted | No negotiate at 3800 or 25, no inferred 3825. Each completed corrected amount is read back and awaits yes. Only the final confirmed total reaches negotiate. Follow the service's counter or agreement. If agreed, hear load/rate, mocked rep handoff, thanks, goodbye and proactive hangup |
| B: notes and ordinary acceptance | On a second supplied available load, listen for all operating conditions, exact free detention period and hourly fee where supplied. Give an ordinary clear total or accept the actual offer | Complete notes before the offer question; no note fee added to the quote. A clear initial amount or direct yes reaches negotiate without an extra readback. On agreement, hear the full truthful handoff/closing and agent hangup |

Both calls can create local reservations. A clear ask can be accepted immediately; there is no promise that a counter is harmless to local availability. Booking sends remain off, so neither call submits to the TMS. You may instead decline before confirming an amount when you only want to test clarification. Do not click Confirm or release a hold without separate approval.

Tell Codex when done, with approximate times or run IDs. Codex will inspect exact tool arguments, timing, hangup and stored records; say whether the full closing was audible, because recordings were not retrievable in the latest review. These checks target the two changed behaviors and intact ending. Your successful Version 6 refusal, repetition, failed-negotiation and time checks remain useful evidence. They do not prove every possible conversation.

## 2. Record the approximately five-minute walkthrough

Use [the run sheet](walkthrough.md). The sequence is: customer problem, one verified live flow, App reservation and timeline, historical pending receipt, separate QA layers, five practical next steps.

Keep the App on **Test** to show your new synthetic call. The **Real calls** KPI cards remain historical and exclude tests. Show Confirm disabled. Use LD01080 in Real Bookings only to illustrate the existing PENDING acknowledgement. Do not send another booking or release a reservation for the video.

Keep the explanation simple: the model conducts the conversation, the service enforces authority/code/rate/round rules, Twin stores the decisions, and the rep owns the irreversible submission. PENDING is an acknowledgement, not a finalized booking. This is a tested proof of concept, not a measured claim of production reliability or financial impact.

## 3. Final submission actions

- Review the refreshed build-description PDF in submission/ready-to-submit/. It is already generated and visually checked.
- Add your video URL to the candidate portal and the submission record. The prospect summary email is drafted in [submission.md](submission.md).
- Approve pushing the local documentation commits. Runtime code is already pushed and deployed; no service deployment is needed for the prompt/documentation change. Workflow publication remains a separate approval.
- Provide/confirm reviewer GitHub handles and approve invitations. The repository is private; the latest read-only access check found only the owner and zero pending invitations. Reviewers also need working HappyRobot workflow/App access. Do not share service keys.
- Review the portal fields, attach the PDF, provide the private repository URL and optionally the prepared source ZIP if useful or requested, and approve submission. Nothing has been uploaded, sent or submitted automatically.

The portal offers repository URL and code ZIP entry, a walkthrough-video URL and file attachments. The assignment still requires a private repository link and reviewer access; a ZIP does not replace that requirement. Its private credential-bearing portal link stays outside the repository. CALL_COHORT can stay synthetic for the demo. Any later cohort or booking-mode change requires separate approval.

## What has already been checked

487 offline service tests, actual 100% service statement/branch coverage, 256/256 business branches, strict types/lint and Radon B or better. The live Version 6 prompt passed 40 checkpoints twice. Unpublished Version 7 passed 51 current checkpoints twice; all failures, fixture corrections and full-text limits are retained. Frontend clean-copy checks pass with 39 tests, three existing lint warnings, production build then typecheck, and zero production dependency vulnerabilities. All 77 App archive files match the checkout. Published App views and both detail panels were reviewed at 1280x900 with no page-level horizontal overflow and every visible Confirm disabled.

The [QA report](qa-results.md), [voice evidence](voice-tuning.md) and [release record](releases/2026-11-04-v6/README.md) preserve versions, failures and limits. The remaining voice acceptance targets the changed Version 7 behavior after approved publication. It does not erase your Version 5 and Version 6 testing or require repeating every earlier scenario.
