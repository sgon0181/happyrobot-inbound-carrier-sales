# Submission candidate

The owner has approved remaining release and submission work. The reviewed fix is live as Version 7, with service release 17 and App Build 20 unchanged. One focused human call and the owner walkthrough video remain; final submission must include those real artifacts rather than claim they are already complete.

## Links and files

| Item | Candidate value | Remaining step |
|---|---|---|
| Private repository | https://github.com/sgon0181/happyrobot-inbound-carrier-sales | Reviewed source through `9d7a149` is pushed; final release/docs update follows. Repository remains private; intended reviewer accounts have not been provided |
| HappyRobot workflow | https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/67nko7p112j2 | Version 7 live since 2026-11-04; prompt SHA-256 `91887bf1ecd2710d07446318f80d144eea55c1aec139cf23c0a812b60720b07b`; one focused human voice call pending |
| Web-call demo | https://platform.happyrobot.ai/deployments/6oaskq84xpfc | Production workflow is Version 7; one focused voice acceptance call pending |
| Operations App | https://carrier-sales-santiago.happyrobot.dev | Carrier Sales, production Build 20, source 48ba398 per Claude; 77-file archive and final 1280px views/panels verified; reviewer-account access remains to check |
| Build description | docs/build-description.md; export in submission/build-description.pdf | Refreshed 3-page PDF generated and all pages visually checked; update only if acceptance changes the claims |
| Walkthrough video | Owner to record and provide URL | Follow walkthrough.md; approximately five minutes |

Repository privacy was verified read-only on GitHub on 2026-11-03: private, default branch main, only the owner listed as collaborator, zero pending invitations. No invitations were sent. Repository access and HappyRobot workspace access are separate; validate both with the reviewers' own accounts. Do not share service keys.

## Summary email to the prospect

Subject: Inbound carrier sales proof of concept and proposed next steps

Hi team,

We built a proof of concept for the first leg of inbound carrier sales. It checks FMCSA operating authority, checks an emailed code, finds matching loads and negotiates within the configured pricing rules. An agreement creates a tentative reservation for a senior rep to review. Transfers are mocked for the web-call demonstration.

The operations App brings the carrier, lane, schedule, posted and agreed payment, negotiation history and next action into one view. It separates reservations, rep-approved submissions, pending TMS acknowledgements, final confirmations and unknown outcomes. Confirm is disabled while booking sends are off.

The service enforces the code gate, rate bounds and three-round limit independently of the model. The ceiling and expected code are withheld from the voice agent; remaining inference and identity limitations are documented. A booking request is sent at most once after rep approval. Our observed successful TMS acknowledgements have returned PENDING, so we do not describe them as final bookings.

We tested the rules offline, generated reproducible pricing and negotiation inputs, repeated unstable conversation checkpoints, and kept complete simulated conversations separate from human voice calls with real integrations. The QA report includes the failures and reruns, exact versions and remaining limits. Production capacity and financial impact have not been established by this demo.

The next steps are to agree the pricing and TMS finalization assumptions; replace the demo inbox with trusted carrier contacts; validate expected capacity and conversation behavior; run a supervised pilot against agreed success criteria; and then consider real telephony and notifications.

Review links:

- Web-call demo: https://platform.happyrobot.ai/deployments/6oaskq84xpfc
- Operations App: https://carrier-sales-santiago.happyrobot.dev
- Private code repository: https://github.com/sgon0181/happyrobot-inbound-carrier-sales

The build description and source ZIP accompany this submission. The walkthrough viewing URL is supplied with the final portal submission. Reviewer repository invitations remain pending the intended GitHub account names.

Thanks,
Santiago

## Reviewer notes

Start with README.md, ARCHITECTURE.md and docs/decisions.md. docs/compliance.md distinguishes the released implementation from remaining acceptance and evidence limits. docs/qa-package.md separates the test layers; docs/qa-results.md records actual counts, versions and remaining failures. docs/kpis.md defines every displayed measure.

The chosen interpretation is to reserve in Twin on agreement and send LOAD_BOOK only at a rep's Confirm. MAX_BUY is provisionally mapped to max_rate, and TMS whole units are displayed as USD. Luke's finalization question remains open in docs/questions.md. PENDING is not final confirmation, and no supported cancel/reset is established. The sandbox is not claimed to have a booking quota.

The shared demo inbox is an approved demonstration exception, not proof of carrier identity. CALL_COHORT is currently synthetic and LIVE_BOOKING is off. Changing either Fly setting requires owner approval. There is no fallback to prototype/e2e.

## Release and access checklist

1. Complete: reviewed prompt fix 9d7a149 published as Version 7 after explicit owner approval; exact root and tool readbacks match. Service release 17 from bf512aa and App Build 20 were not redeployed. Booking sends remain off and calls synthetic.
2. Complete: the owner granted remaining push, release and submission approval. Codex is refreshing release records and the submission package. No extra deployment or booking is needed.
3. Remaining: one focused Version 7 voice call in final-owner-checklist.md. Version 6 refusal, repetition, failed negotiation and times have human evidence and do not need repeating. Retain the new run ID and Twin close/end records.
4. Remaining: owner-recorded approximately five-minute video and its viewing URL. Follow walkthrough.md, hide the emailed code and show the App Test view with Confirm disabled. No cohort flip is required.
5. Reviewer accounts: the portal and latest Luke email thread do not identify GitHub usernames. A private repository and source ZIP are prepared for submission. Invitations remain pending actual recipient identities; do not guess or make the repository public. HappyRobot reviewer-account access is separately unverified.
6. Finalize the portal's repository/workflow/video fields, prospect summary and PDF/source attachments, then submit under the owner's approval when the real call/video are available. Nothing is described as submitted until the portal confirms it.

Historical LD01080 already supplies a PENDING receipt example. The latest reviewed synthetic holds include LD01116 at 3800, LD01112 at 2275, LD01100 at 2050 and LD01102 at 1625. Earlier local declines are preserved in booking history. No further cleanup or TMS send is required.
