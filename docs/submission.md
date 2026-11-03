# Submission candidate

Do not send, push, invite reviewers or submit without owner approval. These texts describe the reviewed candidate; complete the release and voice checks before presenting it as live.

## Links and files

| Item | Candidate value | Remaining step |
|---|---|---|
| Private repository | https://github.com/sgon0181/happyrobot-inbound-carrier-sales | Approve push of the reviewed local candidate; invite specified reviewers |
| HappyRobot workflow | https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/l8x9v2kyt4mc | Version 4 remains unpublished; deploy the service before approving publication |
| Web-call demo | https://platform.happyrobot.ai/deployments/6oaskq84xpfc | Currently Version 3 until Version 4 is approved and published |
| Operations App | https://carrier-sales-santiago.happyrobot.dev | Build 17 remains live until approved App publication and visual review |
| Build description | docs/build-description.md; export in submission/build-description.pdf | Review the candidate facts and generated document |
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

Start with README.md, ARCHITECTURE.md and docs/decisions.md. docs/compliance.md distinguishes local candidate completion from live rollout. docs/qa-package.md separates the test layers; docs/qa-results.md records actual counts, versions and remaining failures. docs/kpis.md defines every displayed measure.

The chosen interpretation is to reserve in Twin on agreement and send LOAD_BOOK only at a rep's Confirm. MAX_BUY is provisionally mapped to max_rate, and TMS whole units are displayed as USD. Luke's finalization question remains open in docs/questions.md. PENDING is not final confirmation, and no supported cancel/reset is established. The sandbox is not claimed to have a booking quota.

The shared demo inbox is an approved demonstration exception, not proof of carrier identity. CALL_COHORT is currently synthetic and LIVE_BOOKING is off. Changing either Fly setting requires owner approval. There is no fallback to prototype/e2e.

## Release and access checklist

1. Claude reviews each local candidate commit and unresolved limits. The owner approves any push; push is a separate action from deployment.
2. Approve and deploy the reviewed service first. Verify authenticated snapshot mode and end-report route without a booking send.
3. Separately approve publishing Version 4, then run the owner voice checklist with authorized email delivery. Leave hostile tests synthetic and booking sends off.
4. Separately approve the App source publication and platform name Carrier Sales. Review it at the demo screen size, including off-mode Confirm, missing historical details, refresh and receipt recovery.
5. Before the demo, separately approve changing CALL_COHORT back to real. A demo booking send requires its own approval for the selected load; historical LD01080 already provides a PENDING receipt example. No new send is required for hostile testing.
6. Obtain the reviewer handles from the candidate portal, approve the invitations, grant the agreed repository access and verify acceptance. Verify the workflow and App open for their HappyRobot accounts too.
7. The owner records the video, inserts its URL, reviews the email and build description, and separately approves submission.

Two synthetic test reservations identified in the handover remain to review and release if appropriate: LD01088 and the reservation from run 8167bb06. Decline releases our reservation without a TMS booking send; do not confuse that with external TMS cancellation.
