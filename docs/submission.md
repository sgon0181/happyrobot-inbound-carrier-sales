# Submission candidate

Do not send, push, invite reviewers or submit without owner approval. The reviewed source has been released with owner approval. Complete the remaining human acceptance, access, video and submission steps below.

## Links and files

| Item | Candidate value | Remaining step |
|---|---|---|
| Private repository | https://github.com/sgon0181/happyrobot-inbound-carrier-sales | Reviewed source `bf512aa` pushed with owner approval; release-docs commit remains local for review; reviewer invitations pending |
| HappyRobot workflow | https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/alj9n98f66df | Version 6 live since 2026-11-04; prompt SHA-256 `287da98f14bd76fccb6c8846af01d9423b3424d86140fa540245b48fd57deef5`; voice checklist pending |
| Web-call demo | https://platform.happyrobot.ai/deployments/6oaskq84xpfc | Production workflow is Version 6; current-version voice acceptance pending |
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

The repository, workflow and dashboard links are above. The build description accompanies the walkthrough. The owner will insert the final video URL before sending this email.

Thanks,
Santiago

## Reviewer notes

Start with README.md, ARCHITECTURE.md and docs/decisions.md. docs/compliance.md distinguishes the released implementation from remaining acceptance and evidence limits. docs/qa-package.md separates the test layers; docs/qa-results.md records actual counts, versions and remaining failures. docs/kpis.md defines every displayed measure.

The chosen interpretation is to reserve in Twin on agreement and send LOAD_BOOK only at a rep's Confirm. MAX_BUY is provisionally mapped to max_rate, and TMS whole units are displayed as USD. Luke's finalization question remains open in docs/questions.md. PENDING is not final confirmation, and no supported cancel/reset is established. The sandbox is not claimed to have a booking quota.

The shared demo inbox is an approved demonstration exception, not proof of carrier identity. CALL_COHORT is currently synthetic and LIVE_BOOKING is off. Changing either Fly setting requires owner approval. There is no fallback to prototype/e2e.

## Release and access checklist

1. Completed with owner approval: Claude reviewed bf512aa and its prompt, then pushed source `bf512aa`. The release-docs commit is local until a separate read-only review and owner approval of its push.
2. Completed by Claude: deploy service release 17, then publish workflow Version 6, verify healthy service, authenticated snapshot and missing-key rejection on `/calls/ended`. Booking sends remain off.
3. Historical: Codex published Carrier Sales App Build 18 from `8b0e483` and recorded its visual checks. The App now shows production Build 20 with the redesigned dashboard. Claude's handover records source 48ba398/import 97da4f6; the 77-file archive matches and final views/panels at 1280px were independently checked. Do not republish without approval. No booking action was clicked in this verification.
4. Complete the three targeted calls in final-owner-checklist.md on exact live Version 6, with separately authorized email delivery. Keep hostile tests synthetic and booking sends off. Preserve run IDs and check the end report in Twin-backed records.
5. Before a real-cohort demo, separately approve changing CALL_COHORT back to real. Any demo booking send needs its own approval for the selected load. Historical LD01080 already supplies a PENDING receipt example; no new send is required for voice or hostile testing.
6. Obtain reviewer handles from the candidate portal, approve invitations, grant agreed repository access and verify acceptance. Verify the workflow and App open for their HappyRobot accounts too.
7. Review the regenerated build-description PDF, record the owner video, insert its URL, review the email and separately approve submission.

All six earlier test reservations have decline events dated 2026-11-04 Sydney. At visual review, five remain Released; LD01100 has since been reserved again by a later synthetic call, with its prior decline preserved in history. The new reservation was left untouched. Decline releases the local reservation; it is not an external TMS cancellation.
