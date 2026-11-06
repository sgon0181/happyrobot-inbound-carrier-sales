# Submission handoff

`main` is the submission source. [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview) is the operating workspace. [Readiness](readiness.md) records the current workflow, service, evidence and remaining release steps. The owner records the final call and five-minute walkthrough using [the exact show/say cues](proposal-demo.md).

## Reviewer package

- Repository ZIP from the final reviewed main commit, with no `.env`, private recordings, credentials, caches or local attachments.
- Demo video showing a genuine call, its matching reservation and the operating report.
- [Build description](build-description.md), [architecture](../ARCHITECTURE.md), [decisions](decisions.md) and [review results](proposal-review.md).
- [QA evidence](readiness.md#evidence-at-a-glance), with original failed grades and exact-version limits retained.
- [One-command local review](readiness.md#reproduce-the-application) for an authenticated App and disposable TMS exercise.

Luke accepted a ZIP upload. A private GitHub link is an alternative, with reviewer access arranged after submission. The owner handles the portal and the final recording; this repository does not claim either was submitted.

## Prospect email

Subject: A carrier desk that qualifies calls and keeps your team in control

Hi team,

I built Carrier Sales around the problems you described: missed opportunities, inconsistent negotiation and agreements that are hard to trace.

The AI agent identifies itself, checks carrier authority, verifies an emailed code, finds matching freight and negotiates within approved limits. A senior rep then reviews the call, shipment and agreed price before authorizing a booking request.

The workspace shows which calls reach a reservation and where others stop. Each measure opens the supporting records, so supervisors can distinguish verification problems, missing freight and unsuccessful negotiations. Pending TMS acknowledgements remain separate from confirmed bookings.

The demonstration includes working calls, an agreement linked to its conversation and documented tests of pricing limits, verification and failure recovery. The test inbox is suitable for this demonstration; a rollout would use your enrolled carrier contacts and named representatives.

For a supervised first shift, I would agree the eligible carrier roster and submission permissions with your team, then measure time to an offer, verified-call conversion and unresolved requests. We can use that evidence to choose where automation should expand and where a rep should intervene.

Best,
Santiago

## Final owner checklist

1. Confirm the deployment state and links in [readiness](readiness.md).
2. Record a new human call on the final tested workflow and retain its exact run ID.
3. Use that same call throughout the App demonstration; keep separate receipt examples clearly identified.
4. Confirm that the ZIP reflects the final reviewed main commit and all required documents.
5. Upload the ZIP and video through the portal. Keep the service available for review, then agree retirement timing with Luke.

## History

The earlier submission source is retained as `oldmain` at `15ce2b6`, with local tag `baseline-v8`. Version 8 and Build 24 evidence remains available for rollback and comparison.
