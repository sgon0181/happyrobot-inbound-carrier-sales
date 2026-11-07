# Release, reproduction and rollback

`main` is the submission source. The operating workspace is [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview), served by `https://happyrobot-proposal-sg.fly.dev`. The populated Twin staging workspace is retained deliberately, including 74 recorded call rows and 19 booking rows at the 22:21 UTC release snapshot (November 6), with later calls appended. The App's hosting slot, workflow deployment and Twin environment are separate settings.

The earlier owner-approved `reciprocal-v2` concession-floor correction from `8ccbf0a` remains in the current service. Before the sandbox Confirm release, on November 7, authenticated health and TMS reachability passed, the snapshot returned 75 calls and 19 booking records, and all 32 runtime source/policy files matched the reviewed source. Guarded sends, demo inbox and Twin staging remain unchanged. [Deployment evidence](../evidence/reciprocal-negotiation/service-deployment-2026-11-07.json) records the image and checks. The owner's first call on the deployed rule, run `6dc95ce1-f7e0-44a3-8394-8408b754527e`, verified MC 138328, matched flatbed LD01114 (Akron, OH to Cedar Rapids, IA) at a $1,100 opening, countered a $1,250 ask with $1,150 and accepted the carrier's $1,175 at the exact amount. The reservation is pending rep review with no TMS send. A second call, run `2e57f13a-6bae-49d9-ae28-845b08db596b`, correctly refused MC 132354 (registration not active) without sending a code.

## Current release state

| Component | Verified state |
| --- | --- |
| Git | Main includes reviewed runtime source `91ad2b7`; old source `15ce2b6` is retained as `oldmain` and local tag `baseline-v8` |
| App | Production Build 11, imported source commit `39f6c01bb804bd64dcdeb20daf1bd980042054ee`; all 91 source files match `91ad2b7:ops-app`, with test, lint, typecheck and build checks passing |
| Service | Source `91ad2b7` deployed to `happyrobot-proposal-sg`; authenticated health, TMS reachability and all 33 runtime/policy hashes verified; 4,032 production Python lines |
| Data | Twin staging; `calls`, `bookings` and the new `negotiations` table; provisioning of negotiation memory verified |
| Voice | [Version 20](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w), ID `01a1b3cf-1025-7c0f-91b6-75f57ce017b4`, slug `zynb7wm66n9w` |
| Workflow Production | Version 20 published and checked by an actual Production call; [Production web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc); Version 19 retained non-live for immediate rollback |
| Sending | `CALL_COHORT=synthetic`, `LIVE_BOOKING=false`; temporary challenge-sandbox permission for MC 138328 from November 7, 03:00 to 15:00 UTC |

The code goes to a demo inbox, so it proves inbox access, not carrier identity; a pilot would enroll real carrier contacts first. The owner authorized a separate challenge-sandbox Confirm demonstration with rep permissions, verified agreement, fresh shipment and ceiling checks, and no retry. It does not enable live carrier booking or change old records. The window expires at **02:00 AEDT on November 8**. Both a call and its current reservation must originate within the window. A new recording after expiry needs a newly authorized window; do not alter timestamps to qualify old calls.

Hosted Confirm on Version 20 run `64404ab5-c89a-4a96-bc65-b27d23e1804a` submitted LD01142 at $3,400 and received **PENDING**, reference `2LCUJMMDOHY4I6UV`. The App displayed it as acknowledged, pending. A stale repeat was rejected; the persisted record retained one confirmation and one send event. The receipt is tied to the actual call, not a fixture. [Sanitized release evidence](../../happyrobot/qa-v20-voice.json) includes the deployed hashes, settings, receipt and local duplicate-send check.

The image is `registry.fly.io/happyrobot-proposal-sg:deployment-01M6T134E2K3B20V5KT63BW24W`, digest `sha256:e8e78bf1668bdf00697c6b7de60db56ad4abf8f0d6e6658d8c6d1eadcf5dd76b`. To disable new sandbox sends, let the window expire or remove all three `SANDBOX_BOOKING_*` settings and restart the service. Preserve receipts and reconcile unresolved sends; never replay them. A full service rollback can restore reviewed `8ccbf0a` with those three settings removed and App Build 10. Workflow Version 20 can stay live because its request contract is unchanged.

## Evidence at a glance

### Current Version 20

[Version 20](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w) is live in Production after owner-approved Development acceptance and independent review. Its protected opening survived overlapping caller audio. A complete verified call retained the supplied lane, used service-approved prices, created a reservation and ended with the exact rate and pending-review status. A separate Production call confirmed routing, authority lookup, delivery to the demo inbox, closure and hangup; its code was not verified. [Readback](../../happyrobot/tool-bindings-v20.json), [audio and audits](../../happyrobot/qa-v20-voice.json), [results and retained failures](../results.md#version-20-release-acceptance).

The final prompt changes only two time-warning passages from Version 19. Version 20 also protects the opening, aligns the search tool schema, centralizes the service URL and enables Northstars. Its final acceptance pass did not change request bodies, authentication or the voice service path; the later sandbox release changes only rep-send authorization and its App presentation. The optional delivery omission in the normal pitch is distinct from the remaining occasional omission of a supplied pickup time in an adversarial checkpoint. No invented time was observed in those checks.

All three `SERVICE_BASE_URL` environment values deliberately use the same demo service and populated Twin staging database. This is not backend isolation. The demo inbox and disabled live carrier mode remain in place, with the separate bounded sandbox permission above. The [bootstrap SQL](../../tools/twin-schema.sql) is for a new workspace; do not reset or reimport the submission database.

To roll the workflow back, publish retained Version 19 (`01a1b2ea-26c8-7131-8252-b334dcaab976`) to Production, explicitly replacing Version 20. Verify the Production pointer and a short call afterward. This workflow rollback does not require a service or App deployment. Development has no live workflow; historical Version 15 remains in Staging.

### Previously recorded release evidence

| Layer | Result | Scope |
| --- | --- | --- |
| Deployed service source | 604 tests; 98.1% business-rule branch coverage; lint, strict types and size/complexity gates pass | Offline rules, contracts, persistence and adversarial behavior |
| Live floor correction | `reciprocal-v2`; all 32 runtime/policy hashes match; four pure pricing smoke cases pass on the deployed machine | Service deployed; owner call `6dc95ce1-f7e0-44a3-8394-8408b754527e` exercised the rule live (see results) |
| Previous Build 10 App | 65/65 tests; lint, typecheck and production build pass | UI and server-route behavior |
| Local end to end | `make review` healthy; one TCP booking; FAKE0001/PENDING shown in the App | Disposable local simulator, not a hosted booking |
| Reciprocal negotiation | Floor correction: extreme asks hold; improving asks inside reach earn bounded movement; retries, reconnects and concurrent-call budgets are retained | [Executed scenarios and review](negotiation.md) |
| Historical Version 15 audio | Three actual diagnostic WebRTC calls overlapped for 176.78 seconds; one agreement and two intentional declines | Exact Version 15 integration, not Version 16 acceptance |
| Historical Version 15 text | 71/74; S5, E6 and TRM failed and retained | Original grading definitions and source hash |
| Final Version 19 text | Raw 70/74 and 73/74; focused 10/10 | Four judge interpretation issues and one genuine early-close limitation remain visible |
| Version 19 voice before floor correction | Full diagnostic journey on deployed `9d051ba`: LD01134 reserved at $3,725 after bounded negotiation | Generated caller, live FMCSA, email, TMS reads and Twin; no booking send |
| Owner human calls | Run `6dc95ce1-f7e0-44a3-8394-8408b754527e` agreed LD01114 at $1,175 after a $1,150 counter; run `2e57f13a-6bae-49d9-ae28-845b08db596b` refused an inactive MC | [Sanitized service records](../evidence/reciprocal-negotiation/owner-calls-2026-11-07.json) |
| Walkthrough video | Pending | Recorded by the owner from the recording script |

The floor-correction pass repeated all four App gates under Node 22.23.4 and exercised browser Confirm against a freshly built disposable stack: exactly one TCP send, FAKE0001/PENDING. All 30 runtime files matched the local source. The owner call and later Version 20 acceptance provide the separate live evidence. [Validation record](../evidence/reciprocal-negotiation/floor-validation.json).

The previous release App checks ran under Node 22 in the repository's Docker image because the host Homebrew Node runtime had a missing library. Production build used `NODE_ENV=production`. A first run inheriting the review image's development value failed; the corrected production build passed. Local validation logs retain both outcomes.

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

Fresh keyed reads batch at their scheduled Twin SQL slot. Writes retain version checks, the service keeps its chosen four-statements-per-second pacing, and voice tools retain their twelve-second deadline. This is the integration's pacing budget, not a general Twin service limit. Historical controlled twelve-call tests completed twelve agreements without unfinished claims after the batching repair. Original failures are retained alongside [simultaneous](../evidence/readiness/capacity-after-simultaneous.json), [staggered](../evidence/readiness/capacity-after-staggered.json) and [history/polling](../evidence/readiness/capacity-maintained-history.json) results.

The new reciprocal memory initially regressed all three controlled twelve-call workloads. A narrow fix avoids a redundant memory write only when a fresh read finds no prior state and the caller accepts the unchanged opening with no rounds spent. Existing memory, lower prices and all concessions retain their writes and CAS. All three reruns completed twelve agreements with zero unfinished claims and zero TMS sends, at unchanged SQL pacing and tool deadline. [Before/after results and limits](capacity.md) retain the failures and the concurrency boundary. These offline opening-acceptance fixtures do not establish peak production capacity or heavy negotiation throughput.

Snapshot reads paginate, reject truncation and stop at a bounded twenty pages; the App permits twenty seconds for snapshots and suppresses overlapping refreshes. Retention and representative arrival-rate testing remain rollout responsibilities.

## What the supervisor can infer

Overview shows recorded stage progress and reservation conversion, with supporting calls. It includes ongoing calls in its displayed denominator and keeps ended-call exceptions separate. Price movement compares agreement with opening, not profit. Imported historical records remain identifiable and view-only. Native recording links require trusted workflow provenance and platform access.

Call data is evidence of recorded service decisions, not proof of every spoken word. The dated sample was dominated by repeated test carriers and cannot establish market conversion, missed-call reduction or financial return. [KPI definitions](kpis.md) specify each boundary.

<a id="native-conversation-evidence"></a>

## Historical conversation evidence

[Version 19 prompt](../../happyrobot/prompt-v19.md) and its fixed initial message identify the AI before asking for an MC. All seven HTTP bindings point to the submission service. The complete native [checkpoint evidence](../../happyrobot/qa-v19-checkpoints.json) records two raw sweeps, **70/74 and 73/74**, plus **10/10 focused consent and exit checks**. No run is pending. Numeric final counteroffers and missing-display fallback both pass twice. Four failed grades are documented judge interpretation issues; they remain failed in the raw evidence.

One genuine limitation remains (R1): after repeated amount clarification, a contradictory response such as "No, it is 110025 dollars" can end the call instead of asking again. It creates no unconfirmed booking, but can lose a valid caller opportunity. This is a known conversational reliability limit, not a green test or an enterprise readiness claim.

Version 15's original [71/74 grades](../../happyrobot/history/qa-proposal-v15-checkpoints.json) remain preserved. E6 run `2a056bd2-b249-445b-80a0-10e417d4b482` lacked thanks inside `close_call._message` under its original criterion. The checkpoint did not prove the later voice hangup farewell. Versioned S5, E6, TRM and V4 criteria now distinguish the caller-facing close message from optional post-close text. Full speech is assessed separately. Later results do not rewrite Version 15's grades.

Version 16's actual voice run exposed an email sent despite a simultaneous request to leave. Versions 17 and 18 distinguish withdrawal from a clear load acceptance followed by a courtesy goodbye. Version 18 then completed a diagnostic voice journey, resisted a ceiling probe, reserved LD01124 at $2,600 and ended with an accurate recap and farewell. [Its sanitized transcript](../../happyrobot/history/qa-v18-voice.json) belongs to that version, not Version 19. [Version 19 speech evidence](../../happyrobot/qa-v19-voice.json) records the complete agreement and a Production routing/exit smoke call. Recognition split the Production caller's name confirmation and goodbye into separate turns, so an email was already initiated before the exit. This does not prove zero sends around interruptions. The fixed disclosure, correct close and automatic hangup were observed. Callers are generated diagnostic audio, not human acceptance; operator pauses are not handling-time measurements.

## Delivery and release boundary

Historically, Version 19 was promoted after its fixed opening, prompt, seven bindings, native checks and complete diagnostic audio journey were verified against service `9d051ba`. Publication required first removing Version 19 from Development, then publishing it to Production while replacing Version 8. Native metadata and the editor both read back Version 19 live in Production. At that earlier release, Development was emptied and Version 15 remained in Staging. No service or App endpoint changed during promotion. At that earlier release, hosted sends were off.

The reviewer-facing links are the Production web call above, the exact Version 20 editor, `https://carrier-sales-proposal-sg.happyrobot.dev/` and `https://happyrobot-proposal-sg.fly.dev`. Authentication remains enabled. Production refers to the workflow deployment; the service deliberately retains Twin staging, synthetic call tags and the approved demo inbox. These settings preserve call history and do not establish carrier identity or authorize live carrier sends. The separate temporary sandbox scope is listed above.

The owner records the walkthrough video and handles portal submission. [The cue sheet](../recording-script.md) follows a real call through its own reservation and authorized sandbox receipt. No completed owner video or portal upload is claimed here.

## Exact release and rollback

Current workflow configuration is recorded in [Version 20 bindings](../../happyrobot/tool-bindings-v20.json) and [audio acceptance](../../happyrobot/qa-v20-voice.json). The current service and App evidence is appended to the Version 20 audio record, without changing the original call evidence. The earlier floor correction remains documented in [its dated deployment record](../evidence/reciprocal-negotiation/service-deployment-2026-11-07.json). Use the immediate Version 19 rollback described above for a workflow-only regression.

The earlier [release manifest](../evidence/release-2026-11-07/release.json), [runtime hashes](../evidence/release-2026-11-07/deployed-service.json), [App checks](../evidence/release-2026-11-07/app-validation.json) and [local Confirm proof](../evidence/release-2026-11-07/local-review.json) are dated evidence, not a new Version 20 service deployment.

## History

The older full stack is source `oldmain` / local `baseline-v8` at `15ce2b6`, Version 8 (`01a1a4f6-79a3-7c40-8732-589b3adfdcfd`) and App Build 24. A deliberate full-stack rollback would restore that workflow with `https://carrier-sales-santiago.happyrobot.dev/` and `https://happyrobot-carrier-sales-sg.fly.dev` as a matched set after checking authenticated health. Do not delete new call records, reinterpret PENDING as BOOKED or replay an uncertain send. Prior [service manifest](../evidence/readiness/deployed-service.json), [native App acceptance](../evidence/readiness/native-app-acceptance.json) and [historical import integrity](../evidence/readiness/historical-import-integrity.json) remain immutable dated evidence.
