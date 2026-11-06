# Release readiness and reproduction

`main` is the submission source. The operating workspace is [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview), served by `https://happyrobot-proposal-sg.fly.dev`. The populated Twin staging workspace is retained deliberately, including 71 recorded call rows and imported history at the latest release snapshot. The App's hosting slot, workflow deployment and Twin environment are separate settings.

## Current release state

| Component | Verified state |
| --- | --- |
| Git | Main includes `cc84d6b`; old source `15ce2b6` is retained as `oldmain` and local tag `baseline-v8` |
| App | Build 10 at the workspace link above; 65 local tests, lint, typecheck and production build pass |
| Service | Updated runtime deployed to `happyrobot-proposal-sg`; authenticated health and TMS reachability verified; 3,850 production Python lines |
| Data | Twin staging; `calls`, `bookings` and the new `negotiations` table; provisioning of negotiation memory verified |
| Voice | Version 16, ID `01a1b2da-1c90-7249-886f-5abb3f2416bf`, slug `42vhesibpud2`, published to Development; repeated checks found ceiling-probe and time/readback defects; successor under preparation |
| Workflow Production | Version 8 until the final release switch is verified; do not use its generic web-call link to record the new behavior |
| Sending | `CALL_COHORT=synthetic`, `LIVE_BOOKING=false`; no hosted Confirm sends are enabled |

The code goes to a demo inbox, so it proves inbox access, not carrier identity; a pilot would enroll real carrier contacts first. The owner explicitly retained this route and disabled hosted booking sends. Demonstrate Confirm in the disposable local App, and identify the earlier [LD01080 sandbox PENDING receipt](https://carrier-sales-santiago.happyrobot.dev/?view=bookings&load=LD01080&run=ddae86e8-c7b0-43b6-8dc1-eb902b45c33f) as a separate historical transaction.

## Evidence at a glance

| Layer | Result | Scope |
| --- | --- | --- |
| Current service | 581 tests; 97.5% business-rule branch coverage; lint, strict types and size/complexity gates pass | Offline rules, contracts, persistence and adversarial behavior |
| Current App | 65/65 tests; lint, typecheck and production build pass | UI and server-route behavior |
| Local end to end | `make review` healthy; one TCP booking; FAKE0001/PENDING shown in the App | Disposable local simulator, not a hosted booking |
| Reciprocal negotiation | Extreme and moderate ladders hold; bounded reciprocal movement, retries, reconnects and concurrent calls pass | [Executed scenarios and review](negotiation-review.md) |
| Historical Version 15 audio | Three actual diagnostic WebRTC calls overlapped for 176.78 seconds; one agreement and two intentional declines | Exact Version 15 integration, not Version 16 acceptance |
| Historical Version 15 text | 71/74; S5, E6 and TRM failed and retained | Original grading definitions and source hash |
| Version 16 | Repeated checks found CAP, S3 and V3 defects | A ceiling probe called negotiate, CST was omitted, and one complete-total readback was vague; release blocked pending repair and retest |
| Final owner recording | Pending | Genuine human call and same-run demo |

The App checks ran under Node 22 in the repository's Docker image because the host Homebrew Node runtime had a missing library. Production build used `NODE_ENV=production`. A first run inheriting the review image's development value failed; the corrected production build passed. Local validation logs retain both outcomes.

## Reproduce the application

Install Docker Compose and Python 3.12, then run:

```bash
make review
```

The command builds the authenticated App, service, identity provider, email and TCP simulator, waits for readiness and opens a reservation. Confirm sends once and displays PENDING. `make review-down` removes only this local environment. No customer credentials or real email are used.

For the cloud service, the target must be explicit:

```bash
make deploy APP=happyrobot-proposal-sg APP_URL=https://carrier-sales-proposal-sg.happyrobot.dev/
```

Do not use an unqualified Fly deployment: the historical `fly.toml` app name points at the rollback service. `make secrets` stages only allowlisted settings. Neither command creates native workflow versions, App builds, Twin tables or carrier contacts. [Onboarding](onboarding.md) describes the access and environment boundaries.

## Concurrency and read budget

Fresh keyed reads batch at their scheduled Twin SQL slot. Writes retain version checks, the service keeps the provider's four-statements-per-second pacing, and voice tools retain their twelve-second deadline. Historical controlled twelve-call tests completed twelve agreements without unfinished claims after the batching repair. Original failures are retained alongside [simultaneous](evidence/readiness/capacity-after-simultaneous.json), [staggered](evidence/readiness/capacity-after-staggered.json) and [history/polling](evidence/readiness/capacity-maintained-history.json) results.

Those measurements preceded reciprocal cross-call memory, which adds storage operations. They do not prove the new runtime's live latency or capacity. Measure it with Version 16 before promotion. Snapshot reads paginate, reject truncation and stop at a bounded twenty pages; the App permits twenty seconds for snapshots and suppresses overlapping refreshes. Retention and representative arrival-rate testing remain rollout responsibilities.

## What the supervisor can infer

Overview shows recorded stage progress and reservation conversion, with supporting calls. It includes ongoing calls in its displayed denominator and keeps ended-call exceptions separate. Price movement compares agreement with opening, not profit. Imported historical records remain identifiable and view-only. Native recording links require trusted workflow provenance and platform access.

Call data is evidence of recorded service decisions, not proof of every spoken word. The dated sample was dominated by repeated test carriers and cannot establish market conversion, missed-call reduction or financial return. [KPI definitions](kpis.md) specify each boundary.

## Native conversation evidence

Version 16 adds the fixed initial message: "You're speaking with an AI agent from HappyRobot Logistics. May I have your MC number?" It also uses the [revised voice prompt](../happyrobot/prompt-proposal-v16.md), correcting email throttling, split MC handling, exits, driving wording, repetitive negotiation and the rep-review explanation. Repeated checks identified three real defects: a private-ceiling probe called negotiate, a time answer omitted CST, and a complete-total readback was vague. A successor is being prepared. Its exact prompt, grades and actual audio must be recorded before Production promotion.

Version 15's [71/74 checkpoint evidence](../happyrobot/qa-proposal-v15-checkpoints.json) is unchanged. Inspection of E6 run `2a056bd2-b249-445b-80a0-10e417d4b482` found that the caller-facing `close_call` message did not thank the caller. That is a real omission under its criterion, not a basis to rewrite the failed grade. S5 and TRM also retain their original definitions and reasons. Any revised criteria and reruns must be appended as new evidence, never substituted for the original scores.

The [Version 15 audio](../happyrobot/qa-proposal-v15-voice.json) and [Version 13 aligned checks](../happyrobot/qa-proposal-v13-checkpoints.json) remain historical comparisons. Their successes do not establish Version 16 behavior. Human acceptance must include the AI disclosure, amounts, agreement wording, actual ending and same-run reservation.

## Delivery and release boundary

Before switching Production, verify the corrected successor's exact graph, prompt, bindings, disclosure and voice outcomes on the deployed service. Check the App's authenticated records and the same call's recording. Keep hosted booking sends off under the owner's chosen demo route. Then publish the tested version to Production, read back the active version and recheck the production web-call entry point. Record that transition here before recording the final demo.

The owner records the final human call and video and handles portal submission. [The cue sheet](proposal-demo.md) keeps a real call, its reservation and separate receipt evidence identifiable. No completed video, upload or new native test score is claimed here.

## History

Version 8, App Build 24 and source `15ce2b6` are retained for rollback. Restore the old workflow Production version and old App/service links together if the new release fails. Do not delete new call records or send an uncertain booking again. Prior [service manifest](evidence/readiness/deployed-service.json), [native App acceptance](evidence/readiness/native-app-acceptance.json) and [historical import integrity](evidence/readiness/historical-import-integrity.json) remain immutable dated evidence, not hashes of the updated runtime.
