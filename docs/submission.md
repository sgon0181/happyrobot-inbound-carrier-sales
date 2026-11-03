# Submission candidate

Do not send, push, invite reviewers or submit without owner approval. The reviewed source has been released with owner approval. Complete the remaining human acceptance, access, video and submission steps below.

## Links and files

| Item | Candidate value | Remaining step |
|---|---|---|
| Private repository | https://github.com/sgon0181/happyrobot-inbound-carrier-sales | Reviewed source `8b0e483` pushed with owner approval; release-docs commit remains local for review; reviewer invitations pending |
| HappyRobot workflow | https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zad4fuknryd8 | Version 5 live since 2026-11-04; prompt SHA-256 `db0ae5ad27f4682296471a335e432f747da53727534e4ebc8f9769656da5ecae`; voice checklist pending |
| Web-call demo | https://platform.happyrobot.ai/deployments/6oaskq84xpfc | Serves Version 5 |
| Operations App | https://carrier-sales-santiago.happyrobot.dev | Carrier Sales, Build 18, source `8b0e483`; published visual check recorded in qa-results.md |
| Build description | docs/build-description.md; export in submission/build-description.pdf | Review current release facts and regenerate the PDF from the updated Markdown before submission |
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

The repository, workflow and dashboard links are above. The build description accompanies the walkthrough. The owner will insert the final video URL before sending this email.

Thanks,
Santiago

## Reviewer notes

Start with README.md, ARCHITECTURE.md and docs/decisions.md. docs/compliance.md distinguishes the released implementation from remaining acceptance and evidence limits. docs/qa-package.md separates the test layers; docs/qa-results.md records actual counts, versions and remaining failures. docs/kpis.md defines every displayed measure.

The chosen interpretation is to reserve in Twin on agreement and send LOAD_BOOK only at a rep's Confirm. MAX_BUY is provisionally mapped to max_rate, and TMS whole units are displayed as USD. Luke's finalization question remains open in docs/questions.md. PENDING is not final confirmation, and no supported cancel/reset is established. The sandbox is not claimed to have a booking quota.

The shared demo inbox is an approved demonstration exception, not proof of carrier identity. CALL_COHORT is currently synthetic and LIVE_BOOKING is off. Changing either Fly setting requires owner approval. There is no fallback to prototype/e2e.

## Release and access checklist

1. Completed with owner approval: Claude reviewed the fixes and final prompt, then pushed source `8b0e483`. The release-docs commit is local until Claude reviews it and the owner approves its push.
2. Completed by Claude: deploy service release 16, publish workflow Version 5, verify healthy service, authenticated snapshot and missing-key rejection on `/calls/ended`. Booking sends remain off.
3. Completed by Codex: publish Carrier Sales App Build 18 from `8b0e483`, rename the existing App, and record the published visual checks and screenshots in qa-results.md. No booking action was clicked.
4. Complete the owner voice checklist on exact live Version 5, with separately authorized email delivery. Keep hostile tests synthetic and booking sends off. Preserve run IDs and check the end report in Twin-backed records.
5. Before a real-cohort demo, separately approve changing CALL_COHORT back to real. Any demo booking send needs its own approval for the selected load. Historical LD01080 already supplies a PENDING receipt example; no new send is required for voice or hostile testing.
6. Obtain reviewer handles from the candidate portal, approve invitations, grant agreed repository access and verify acceptance. Verify the workflow and App open for their HappyRobot accounts too.
7. Regenerate and review the build-description PDF, record the owner video, insert its URL, review the email and separately approve submission.

All six earlier test reservations have decline events dated 2026-11-04 Sydney. At visual review, five remain Released; LD01100 has since been reserved again by a later synthetic call, with its prior decline preserved in history. The new reservation was left untouched. Decline releases the local reservation; it is not an external TMS cancellation.
