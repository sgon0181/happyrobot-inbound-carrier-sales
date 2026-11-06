# Layered QA package

These layers answer different questions. Generated pricing inputs are not calls, a scripted HTTP journey is not an LLM conversation, and a model's grade is not a proof. Current results are in [results](../results.md); the deployed release is recorded in the [release guide](release.md).

## Historical baseline package, November 4

The table and checklist below retain the released Version 8 package and earlier App evidence. Their counts and instructions are historical, not the current release or recording plan. At that time automated tests and native simulations used fake or locked integrations; the later actual V15 audio is recorded separately.

| Layer | Baseline evidence | Reproduce or review | Limits |
|---|---|---|---|
| Automated service tests | 487 passed; 1650 statements and 406 branches, all covered; gated 256/256 | make check; service/tests/ | Network guard permits loopback only. Fakes do not prove live capacity or integration contracts |
| Randomized pricing inputs | 20,000 generated loads, seed 7 | test_pricing.py::test_the_rules_hold_across_many_loads | Posted100..12000, ceiling70%..130% of posted; unpriceable inputs are skipped, with more than19000 priced asserted. No model, speech or TMS |
| Randomized negotiation setups | 5,000 generated setups, seed 11 | test_negotiation.py::test_no_rate_above_the_cap_is_ever_offered_or_accepted | Posted500..9000, ceilings600..11000, asks1..20000, up to5 decisions until terminal. Unpriceable setups are skipped; not5000 calls |
| Conversation checkpoints | Version 8: 59 definitions twice, 118/118 native grades; focused 8 cases three times 24/24. Earlier versions and failed/rerun batches remain historical | happyrobot/qa-v8-confirmation-regression.json, prompt-v8.md and earlier evidence | Six actions locked per case. Scripted checkpoint histories do not test speech or the end callback |
| Complete HTTP service journeys | Nine scenarios through real routes and fake integrations | service/tests/test_journeys.py | Includes3 equipment/lane/carrier combinations. A scripted driver supplies user decisions; no LLM, audio or spoken handoff is measured |
| Full model conversations | Version 8: two inspected complete recording replays with exactly 1125 after corrected readback and explicit Yes; historical conversations retained | happyrobot/qa-v8-recording-replays.json and prior simulation files | All 7 external actions locked. Text ending differs from voice and omits recorded final speech; no voice pass inferred. Fixed outputs are not stateful backend validation |
| Human voice calls | Historical real-integration calls; reviewed Version 5, eleven Version 6 and recorded Version 7 failure traces; owner-reported successful normal Version 8 call | qa-results.md; final-owner-checklist.md | Latest Version 8 success is an owner report; no independent transcript/audio review or live split-number retest is claimed |

## Scenario inventory

| Risk or scenario | Evidence |
|---|---|
| Verification through agreement and end | Three complete HTTP journeys; S5 checkpoint; native standard simulation (one text run) |
| Ineligible carrier versus unavailable FMCSA | Complete terminal HTTP journeys; E1/E2 checkpoints |
| Wrong/expired code and resend | Each standard HTTP journey; test_verify and test_codes |
| Caller changes code destination | HTTP journey rejects extra email field before sending anything |
| Urgency or administrator bypass | A2/A4 checkpoints; HTTP extra-state/unauthorized-search refusal; native pressure run (urgency/code refusal only; idle timeout, not a clean close) |
| Ceiling fishing and instruction pressure | A1/A4/A6 checkpoints; marked-value exclusion and generated pricing/negotiation bounds. No claim of zero indirect inference |
| MC/load changes reset budgets | Complete HTTP journey uses two loads and three MCs; test_verify preserves code budgets |
| Vague/corrected/repeated/final rates | E6/E8 repeated checkpoints; test_money, test_selling and complete limit-switch journey |
| No match, disappearing load, read outage | Complete HTTP journeys, E4 and E7a/b/c checkpoints |
| Interrupted or pre-tool call | test_activity end-before-tool; journey with agreement but no model close; honest absent notes |
| Uncertain send, duplicate send, stale rep screen | test_book and test_rep_actions inject faults using loopback/fake adapters; no live load consumed |
| Receipt arriving after row movement/outage | npm test exercises actual recovery components with fake fetch/storage/timers |

## Historical human voice acceptance checklist

Service release 17 and workflow Version 8 are live. The owner reports that the normal Version 8 demo call worked. No repeat of the superseded Version 7 stress-call script or successful Version 6 suite is required. The confirmation defect is covered by recording-derived checkpoints and two complete mocked replays. The split-number edge case has not been retested through live speech; the latest normal call has not had an independent transcript/audio review. Keep these evidence levels distinct. Calls remain synthetic and booking sends remain off. No new booking is needed.

Recorded outcomes must distinguish observation from inference. A saved reservation is not proof a handoff was spoken. An emailed code to the shared inbox is not carrier identity. An end report does not recreate absent notes. Call-start-to-spoken-offer timing and capacity remain unproven.

## Historical review and release

Preserve historical failures and setup errors. Reconcile case IDs, versions, fixture shapes, run IDs and denominators before presentation. A fresh service or prompt change requires the relevant regression layer, not an inflated combined test count. Build 20's then-current read-only visual evidence is in the release record; Build 18 remains historical. The owner-reported Version 8 normal-call success remains separate from independently reviewed traces and automated test results.

Frontend evidence: 39 tests, lint 0 errors / 3 existing warnings, production build then typecheck, and zero production dependency vulnerabilities in a clean Node 22 container. Build precedes typecheck because Next generates image declarations. All 77 then-current App archive files match the checkout. Published Build 20 overview, queue, bookings, calls, demand and both detail panels were checked at 1280x900, including Real/Test switching, disabled Confirm and the historical PENDING receipt. No Confirm, Decline or Reconcile was clicked. Receipt recovery and error recovery remain component-tested.

Historical full-suite result: 18/22 cases passed all three runs (58/66); failures remain in their original evidence. The subsequent fixed Version 4 passed 44/44. Final Version 5 passed all 23 cases twice (46/46) and was published with owner approval. These historical model grades do not become current-version voice evidence.
