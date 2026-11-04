# Submission candidate

Current dashboard release: **App Build 22**, reviewed source `8ff094a` (clarity change `7262be4` plus explicit empty-field labels). Workflow Version 8 and service release 17 are unchanged. The 80-file source import, 49 frontend tests, checks and live visual review are in [dashboard release](releases/2026-11-04-dashboard-clarity/README.md). Earlier App build/source descriptions below are historical. No voice retest, cohort change or new booking is required.

The owner controls final submission and explicitly directed Codex to leave the portal alone. No portal fields, uploads, access grants or submission are authorized. Workflow Version 8 and service release 17 are unchanged; App Build 22 is live. [Verification and limits](confirmation-fix.md) cover the recorded confirmation regression. The owner reports a successful normal Version 8 call; no independent transcript/audio review of that latest call is claimed. The walkthrough video URL and reviewer access remain to be finalized.

## Links and files

| Item | Candidate value | Remaining step |
|---|---|---|
| Private repository | https://github.com/sgon0181/happyrobot-inbound-carrier-sales | Reviewed Version 8 source and release records are pushed; the refreshed package manifest pins its exact source commit. Repository remains private; intended reviewer accounts have not been provided |
| HappyRobot workflow | https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/kvexhw5fzj4y | Version 8 live since 2026-11-04; prompt SHA-256 `53a884aea629114fa6d3342b9c8cf9f392bf376ca053622ab1f561821d33437c`; 118/118 locked checkpoints and two complete mocked recording replays |
| Web-call demo | https://platform.happyrobot.ai/deployments/6oaskq84xpfc | Production workflow is Version 8; owner reports successful normal demo call, not independently reviewed |
| Operations App | https://carrier-sales-santiago.happyrobot.dev | Carrier Sales, production Build 22, reviewed source 8ff094a; exact 80-file import and 1280px views/panels checked; reviewer-account access remains to check |
| Build description | docs/build-description.md; export in submission/build-description.pdf | PDF regenerated from corrected Version 8 source and visually checked; exact source/PDF hashes are in the local package manifest |
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
2. Complete: reviewed Version 8 confirmation fix eaa2661 published under existing non-portal release approval, with exact post-publication root/tool readbacks. Service 17 and App 20 unchanged. The owner withdrew portal-writing authorization.
3. Specific Version 7 confirmation failure reproduced and fixed using the recording. Version 8 passes 118/118 locked checkpoints and two complete mocked replays. The owner reports that the normal Version 8 call worked. No independent transcript/audio review or live split-number retest is claimed. Do not repeat the superseded stress script.
4. Remaining: owner-recorded approximately five-minute video and its viewing URL. Follow walkthrough.md, hide the emailed code and show the App Test view with Confirm disabled. No cohort flip is required.
5. Reviewer accounts: the portal and latest Luke email thread do not identify GitHub usernames. A private repository and source ZIP are prepared for submission. Invitations remain pending actual recipient identities; do not guess or make the repository public. HappyRobot reviewer-account access is separately unverified.
6. Owner only: finalize portal fields, attachments and final submission. Codex must not interact with the portal. No new upload or completed submission is claimed.

Historical LD01080 already supplies a PENDING receipt example. The latest reviewed synthetic holds include LD01116 at 3800, LD01112 at 2275, LD01100 at 2050 and LD01102 at 1625. Earlier local declines are preserved in booking history. No further cleanup or TMS send is required.
