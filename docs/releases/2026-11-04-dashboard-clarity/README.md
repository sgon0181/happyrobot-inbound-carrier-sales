# Carrier Sales dashboard clarity release

Owner-approved App-only release on 2026-11-04 Sydney. Production App Build 22 uses reviewed Tech-Challenge source `8ff094a`, consisting of dashboard clarity `7262be4` and the empty-field correction. Workflow Version 8, Fly service release 17, pricing, authentication and secrets are unchanged. Booking sends remain off and calls remain synthetic. No booking action or submission-portal interaction was performed.

## What changed and why

The assignment asks an operations manager to understand and act without raw platform logs. The previous overview displayed an unexplained Northstar percentage, mixed historical milestones with current states, and retained real-only metrics inside Test scope.

- Current work comes first: reservations awaiting rep review, unknown submission outcomes, pending acknowledgements and final TMS confirmations.
- Real/Test selection and all-recorded-history scope are visible above the content. Test view contains test results only.
- Historical conversion says what it measures and shows its numerator, denominator and small-sample limit. The mixed-unit funnel is removed.
- Reservation details lead with carrier, lane, agreed payment and next action. Confirm remains disabled when sends are off or unknown.
- Call activity uses readable amounts, shipment times and rounds. Technical references are expandable. Empty shipment text explicitly says Not recorded, and pitched free-form notes are redacted.

## Source, checks and review

The source archive has 80 files, independently hashed locally and verified in the existing Apps sandbox against its manifest, both as working files and committed blobs. The native Production action publishes this existing App; no new App or workflow version was created. Detailed source and import identifiers are in release.json.

49 frontend tests, lint with zero errors and three pre-existing warnings, production build, typecheck and a zero-vulnerability production dependency audit pass on Node 22. Service make check passes 487 tests with 100% of 1650 statements and 406 branches; business branches are 256/256. Python Radon maximum is 10, rank B. Both code commits received a separate read-only review with no findings.

Production source is 2919 Python lines and 4666 App TS/TSX lines. The largest custom App module is 239 lines. The unchanged template sidebar remains a 726-line baseline exception. Validation numbers and limits are in validation.json.

## Live read-only acceptance

The production build selector, Real and Test overview, reservation panel, call activity, long outcomes and historical PENDING record were inspected. At 1280px there is no page-level horizontal overflow. Real conversion remains 1 of 3 recorded email-verified calls, 33%; Test history is separate. All nine visible queue Confirm buttons are disabled. No Confirm, Decline or Reconcile was clicked. Saved screenshots are local evidence, outside the hand-in folder.

A first live visual check found blank shipment notes, corrected in the reviewed 8ff094a follow-up before this final release. There is no new voice acceptance requirement for this frontend-only change.

## Limits and delivery

This release improves the communication of existing records. It does not repair missing activity capture, prove carrier identity from the demo inbox, establish production capacity or prove zero indirect ceiling inference. Receipt recovery remains component-tested. No production failure or TMS booking was injected.

The build description, source ZIP and recording guide are refreshed for this App build. Use the existing successful Version 8 call footage. The owner still supplies the video URL, verifies intended reviewer access and performs the final portal submission. No new call, cohort change or booking is required.
