# Proposal readiness and reproduction

This source belongs to `ultimateProposal`. Production remains on the preserved Version 8 voice workflow and Build 24 App. The newer voice candidate runs in a separate development environment against the proposal service and Twin staging. Development is not production. The final candidate evidence is recorded separately from the earlier V9 and V10 results; scores never transfer between prompt versions.

The proposal service uses `TWIN_ENVIRONMENT=staging`, `CALL_COHORT=synthetic` and `LIVE_BOOKING=false` for actual voice acceptance. Production's 50 call rows and 15 booking rows were copied into staging with immutable import metadata. Both originals and imported content were checked. The [final read-only integrity check](evidence/readiness/historical-import-integrity.json) confirmed all 50 production calls and 15 production bookings were unchanged, and all imported copies remained unchanged after acceptance calls. A released historical row cannot be recycled by a fresh call. New calls add genuine records to the same workspace. All recorded rows are visible by default, without a trial/desk switch.

Deployment names describe separate resources: the new [candidate App](https://carrier-sales-proposal-sg.happyrobot.dev/) uses its own HappyRobot Apps Production hosting slot. Its server points to the isolated proposal service backed by Twin **staging**. The candidate voice version is published only to workflow **Development**. The original Carrier Sales App and workflow Production Version 8 are unchanged. A new App's Production hosting label does not promote the service data or voice workflow to the baseline environment.

Native [candidate Build 10](https://carrier-sales-proposal-sg.happyrobot.dev/) is accepted for isolated review. Its deployed tree matches all 91 reviewed App files, including the canonical package metadata and verified native identity fix. Hosted authenticated health returned 200, omitted credentials returned 401, and the assigned rep reached request validation while a foreign-origin request was refused. No real hosted booking write was used for this check. The fresh Version 15 LD01123 recording link opened the matching development run, audio and transcript. [Exact native acceptance record](evidence/readiness/native-app-acceptance.json) preserves source hashes, prior rejected imports, the scope of native assistant hash evidence and baseline Build 24 verification.

**Source versus later documentation.** The immutable native 91-file and deployed service 33-file manifests below identify the accepted 9e846c0/c923f27 source snapshot. The subsequent architecture consolidation updates `ops-app/README.md` and `service/README.md` without redeployment. Those two documentation files intentionally differ from their hosted snapshot; executable code, configuration, policy files and voice artifacts are unchanged. Do not describe the later checkout as byte-identical in its entirety or rewrite the original evidence hashes.

## Evidence at a glance

| Evidence layer | Observed result | What it establishes |
| --- | --- | --- |
| Actual Version 15 voice, automated diagnostic callers | Three overlapping calls, 176.78 seconds together. Agreement, corrected-price decline and final-offer refusal all ended through the agent. Zero TMS booking sends. | Bounded real integration and audio scenarios, not human naturalness or production capacity. |
| Native Version 15 text checkpoints | 71 passed, three failed of 74; failed grades retained. | Tool and response checks, with explicit grading-boundary limitations. |
| Paced fixture integration | Twelve of twelve agreements in both controlled arrival patterns after the contention repair; no unfinished claims. | This isolated workload at four SQL statements/second and a twelve-second tool deadline. |
| Source gates | 563 service tests, 97.9% business branches; 65 App tests plus build/types/lint. | Deterministic rules, API contracts and UI behavior. |
| New owner human call | To be recorded using the final tested candidate. | The actual human experience and same-run demonstration; do not replace with diagnostic speech. |

## Reproduce the application

Install Docker with Compose and Python 3.12. From the repository root:

```bash
make review
```

The command builds this source, starts the disposable local identity provider, service and Next App, waits for readiness, then opens `http://127.0.0.1:3081/enter/rep`. There is one clearly identified local fixture reservation. Review its shipment, confirm it, and inspect the returned PENDING acknowledgement. The TCP simulator receives exactly one booking command. The viewer entry at `http://127.0.0.1:3081/enter/viewer` has no mutation permission. `/counts` on that local entry service exposes the simulator's booking-command count and current state.

No `.env`, production credentials or historical personal export is mounted. Twin, authority and email use local fixtures. Confirmation exercises the service and a real loopback TCP listener. It does not prove the external TMS or live carrier identity. Both exposed ports bind to `127.0.0.1`; the dedicated Docker bridge is not an egress firewall. Building images and dependencies requires internet access. This local review uses Next development mode with a private fixture identity provider, without weakening production origin or authentication checks. If no GUI browser is available, the command prints the ready URL.

`make review-down` stops only this Compose project and removes its disposable certificate volume. Re-running `make review` recreates its state and certificate. No local review command publishes an App or workflow.

Final independent acceptance ran `make review` on a clean source copy using the observed native `id` identity shape, opened the real browser confirmation dialog and accepted it. The UI showed the PENDING receipt `FAKE0001` and authenticated fixture rep. A stale repeat returned `stale`; a viewer received HTTP 403. The simulator counted exactly one booking command after all checks. [Browser and route evidence](evidence/readiness/local-browser-acceptance.json). The missing Next development-origin allowlist was found through this browser test and repaired; rendering HTML alone had not demonstrated working controls. Native acceptance later exposed a separate identity-contract error: the actual platform returns `id`, while the original local fixture returned `sub`. The adapter now validates and normalizes the verified native ID, rejects conflicts, and the fixture uses the observed `id` shape. The route-level regression exercises that real adapter before rep authorization.

For a preconfigured isolated Fly target and HappyRobot App:

```bash
make secrets APP=<isolated-fly-app> APP_URL=<native-app-https-url>
make deploy APP=<isolated-fly-app> APP_URL=<native-app-https-url>
```

The first command stages only listed service settings from `.env` and the environment. The deployment command uses the repository Dockerfile, including required policy JSON, deploys to the explicit target, checks authenticated service health and TMS reachability, then opens the named App only after readiness. It refuses an omitted target. Supply the matching `OPS_API_KEY` for that readiness check. Deployment is one command after resource and secret provisioning; it does not create native workflow nodes, Twin tables, HappyRobot Apps or an enrolled contact roster. Provision `calls` and `bookings` in Twin staging, point candidate tools at the isolated service, and configure that App's origin and service URL before using it. [Pilot settings](proposal.md#pilot-configuration-and-rollback) list the remaining controls.

The exact isolated deployment command was exercised successfully:

```bash
make deploy APP=happyrobot-proposal-sg APP_URL=https://carrier-sales-proposal-sg.happyrobot.dev/
```

Authenticated health and TMS reachability passed before the browser opened. All 33 remote runtime, requirements, policy and service README files matched the final source snapshot, including the delayed-replay metadata fix. Settings remained staging, synthetic and sends disabled. [Sanitized deployment manifest](evidence/readiness/deployed-service.json). This proves the service deploy/open path; native App hosting and login are checked separately.

## Concurrency and read budget

The original service respected the provider's four-statements-per-second budget but repeatedly reread individual rows. Under contention, legitimate calls timed out. Fresh keyed reads now join a batch while waiting for the scheduled SQL slot. That batch detaches before execution; a later reader or conflicted update gets a later snapshot. Writes remain version checked and independent. Tests cover cancellation, query failure, freshness after a write, isolated result objects, conflicting reservations and bounded admission.

The original twelve-second voice deadline and 0.25-second SQL pacing remain unchanged. There is no throughput increase from bypassing either constraint.

| Controlled full-flow workload | Before | After fresh-read batching |
| --- | --- | --- |
| 12 simultaneous arrivals, no think time | 11 reached matching, 0 agreement replies, 184 SQL, 11 unfinished claims | 12 agreements, 145 SQL, 0 unfinished claims; negotiation p95 10.29 s, journey p95 36.15 s |
| 12 arrivals 1.5 s apart, 3 s between tools | 12 matched, 6 agreement replies, 251 SQL, 9 durable holds and 6 unfinished claims | 12 agreements, 189 SQL, 0 unfinished claims; negotiation p95 8.54 s, journey p95 39.91 s |
| Same staggered workload plus 500 historical calls, 200 released bookings and snapshot polling | Not a paired baseline measurement | 12 agreements, 204 SQL, 0 unfinished claims; negotiation p95 10.04 s, journey p95 41.65 s |

These are single-run local integration observations, not production peak capacity. Authority, mail and Twin are fixtures, with genuine service code and loopback TMS transport. No booking is submitted in the paced profile. Every successful result has a finalized source-call agreement; an incomplete hold cannot be confirmed. The separate competing-rep test submits twelve simulated bookings once each despite 24 approvals.

Raw results preserve the failures: [simultaneous before](evidence/readiness/capacity-before-simultaneous.json), [staggered before](evidence/readiness/capacity-before-staggered.json), [simultaneous after](evidence/readiness/capacity-after-simultaneous.json), [staggered after](evidence/readiness/capacity-after-staggered.json), and [independent history probe](evidence/readiness/capacity-independent-history.json). The history probe's original `durable_holds: 212` field counted all booking rows, including 200 released imports; only twelve were new reservations. The maintained harness separates `booking_rows` from reserved `durable_holds`.

Reproduce with Python 3.12 and the development dependencies:

```bash
python -m service.tests.full_profile --arrivals 12 --spacing 0 --think 0
python -m service.tests.full_profile --arrivals 12 --spacing 1.5 --think 3
python -m service.tests.full_profile --arrivals 12 --spacing 1.5 --think 3 --historical-calls 500 --historical-bookings 200 --dashboard
```

Each command reports outcomes, per-tool and journey p95, actual SQL statements, outstanding claims, finalized agreements and wire writes. The optional dashboard loop waits fifteen seconds after each completed snapshot and ends with the callers. Timings vary by host and current revision. The independently captured history probe stopped its snapshot loop when its first caller completed; its raw observation remains unchanged. The [maintained harness rerun](evidence/readiness/capacity-maintained-history.json), polling until all callers finished, also completed 12/12 agreements with no unfinished claims or booking writes. It used 213 SQL statements, negotiation p95 10.04 seconds and journey p95 41.92 seconds. Its three snapshots took 3.03, 14.59 and 4.57 seconds; the additional refresh accounts for the extra nine reads.

The history probe exposed a second issue: one snapshot took 14.59 seconds, exceeding the old App's ten-second budget. The App now gives operations reads twenty seconds and suppresses overlapping refreshes while keeping the prior snapshot time visible. An actual Next route with a 14.6-second delayed service rendered the reservation in 14.70 seconds. A 21-second delay produced truthful unavailability at 20.08 seconds; the next immediate response recovered in 0.08 seconds. [Measured results](evidence/readiness/app-snapshot-deadline.json). These route tests do not claim browser interaction or voice performance.

Twin's live SQL API was separately observed truncating at 500 rows and at one million response bytes. The adapter scans ordered 100-row pages, rejects truncation metadata and non-increasing identifiers, and stops after twenty pages per table. Twenty full pages, including exactly 2,000 rows, are deliberately unavailable rather than accepted as complete. Oversized pages also fail closed. There is no claim of unlimited retention or cross-table transaction consistency. The cache expires five seconds after refresh completion. Growing history, event size, multi-instance quotas and real arrival patterns need a measured retention and capacity plan before production rollout.

## What the supervisor can infer

- Overview includes stage progress across all recorded native calls. The conversion denominator explicitly includes ongoing calls. Ended-call exceptions require actual end evidence; ongoing or missing-end calls have a separate drilldown.
- Imported trials and fresh development calls remain identifiable. Repeated test carriers are disclosed. The original nineteen-agreement sample was dominated by one carrier, so it cannot estimate market conversion or broad carrier satisfaction.
- Price movement is the difference between agreement and opening, not profit or savings against an invented benchmark. Ceiling compliance comes from deterministic code and test evidence, not a hardcoded zero card.
- A PENDING response is acknowledged, never promoted to BOOKED. A real Confirm requires an assigned rep, a fresh valid shipment, completed consent, trusted identity and explicit enabled sends. Historical imports are view-only even if a copied state said RESERVED or RELEASED.
- Fresh native recordings use configured workflow provenance stamped when the call is created. A random UUID is not enough to construct a recording link. Access still depends on the reviewer's HappyRobot permissions.

## Native conversation evidence

The final candidate is Version 15, ID `01a1a92c-4218-7de5-a2ca-6aca7b2d951e`, slug `4l79y6ugq62q`, published only to development. Its root prompt SHA-256 is `610f904bf08fba2bd831477c5c055c5a52d855a6be9605ccf4c9f922a5503b45`. The [prompt](../happyrobot/prompt-proposal-v15.md), [tool bindings](../happyrobot/proposal-tool-bindings-v15.json) and [checkpoint evidence](../happyrobot/qa-proposal-v15-checkpoints.json) identify this exact revision.

The native matrix graded 71 passed and three failed out of 74 locked text checkpoints. The failures remain S5, E6 and TRM; no adjusted 74/74 score is claimed. S5's judge treated a criterion excluding farewell scoring as a prohibition against a farewell, which the criterion does not say. E6 and TRM's reasoning acknowledge the appropriate tool/message but reject the missing final text continuation. This is consistent with the native tool-checkpoint boundary, but a complete checkpoint trace was not exposed, so independent trace inspection is not claimed. Exact-version actual audio is the separate test of spoken recap and termination.

The [Version 13 aligned matrix](../happyrobot/qa-proposal-v13-checkpoints.json) passed 73/73, but that score belongs only to Version 13. Eight criteria were explicitly versioned there: one asks for one missing detail at a time, and seven judge the caller-facing business message at the native checkpoint boundary while leaving audible farewell and transport termination to full audio acceptance. A normal fixture now includes the service's authoritative display timestamps; the separate missing-label adversarial check remains. Earlier V10/V11/V12 grades and assertion changes are preserved.

Live Version 13 audio exposed a search before a partially transcribed lane was complete, despite its text score. Two calls reserved and ended; a third diagnostic caller stalled in speech synthesis and is not counted as a pass. The successor added an explicit lane gate and a dedicated missing-lane checkpoint. This is why text grades alone do not establish conversation readiness. The [exact Version 15 audio acceptance](../happyrobot/qa-proposal-v15-voice.json) completed all three actual WebRTC calls with a single close, one goodbye and agent hangup. They overlapped for 176.78 seconds. One agreed to $2,100 for LD01123 and heard the exact pending-rep recap. One corrected a relative amount, received fresh total readbacks, then declined without a negotiation or reservation. The third waited for the missing lane, rejected a private-ceiling probe, used three counter rounds, and closed on explicit final refusal without handoff. All three passed their first OTP attempt. FMCSA, approved demo-inbox delivery and safe TMS reads were live; Twin writes used staging and booking sends stayed disabled.

These calls used the recorded guarded batching runtime snapshot. The final source also repairs metadata on a delayed earlier counter after round three: it now reports the current final offer and round rather than the old round label. That later branch has focused and full service regression evidence; the audio scenarios do not claim to exercise it. [Earlier voice and harness failures](../happyrobot/qa-proposal-voice-history.json) remain recorded.

This demonstrates three overlapping integration journeys, not a production capacity or AHT target. Manual orchestration and sequential inbox reads contribute to the 178, 251 and 328 second durations. Generated diagnostic callers do not establish human accent/noise coverage or subjective naturalness. The owner script still requires a genuine new human call before submission. No submission video or generated narration is provided. Production remains on Version 8.

## Delivery and release boundary

[The five-minute script](proposal-demo.md) provides exact owner SHOW/SAY cues with two call-length budgets. It requires a new human call and the same run's reservation and media. No synthetic narration or video is generated by this script. If no agreement occurs, the alternative narration shows the real exception. Any separate simulator receipt is labeled separately.

Before production promotion, review the exact final native prompt and bindings, actual voice outcomes, release configuration and representative concurrent calls. The local capacity experiment does not replace those checks. Production contact enrollment, rep assignment, operations ownership, TMS finalization and measurable telephony/hold baselines remain explicit pilot responsibilities. Main, the original submission ZIP and the published baseline are preserved until a separate release decision.
