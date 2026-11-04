# Layered QA package

These layers answer different questions. Generated pricing inputs are not calls, a scripted HTTP journey is not an LLM conversation, and a model's grade is not a proof. All new automated tests and native simulations use fake or locked integrations. No live booking is part of this package.

| Layer | Current evidence | Reproduce or review | Limits |
|---|---|---|---|
| Automated service tests | 487 passed; 1650 statements and 406 branches, all covered; gated 256/256 | make check; service/tests/ | Network guard permits loopback only. Fakes do not prove live capacity or integration contracts |
| Randomized pricing inputs | 20,000 generated loads, seed 7 | test_pricing.py::test_the_rules_hold_across_many_loads | Posted100..12000, ceiling70%..130% of posted; unpriceable inputs are skipped, with more than19000 priced asserted. No model, speech or TMS |
| Randomized negotiation setups | 5,000 generated setups, seed 11 | test_negotiation.py::test_no_rate_above_the_cap_is_ever_offered_or_accepted | Posted500..9000, ceilings600..11000, asks1..20000, up to5 decisions until terminal. Unpriceable setups are skipped; not5000 calls |
| Conversation checkpoints | Current Version 6: 40 definitions twice, 80/80. Version 5: 46/46 and earlier failed/rerun batches remain historical | happyrobot/qa-v6-audit-fixes.json, prompt-v6.md and earlier evidence | Six actions locked per case. Scripted checkpoint histories do not test speech or the end callback |
| Complete HTTP service journeys | Nine scenarios through real routes and fake integrations | service/tests/test_journeys.py | Includes3 equipment/lane/carrier combinations. A scripted driver supplies user decisions; no LLM, audio or spoken handoff is measured |
| Full model conversations | Historical Version 4 pair plus retained Version 6 iterations; latest refusal and compound agreement reach close and text ending without another caller turn | happyrobot/qa-v6-audit-fixes.json and prior simulation files | All 7 external actions locked. Text ending differs from voice and omits recorded final speech; no voice pass inferred. Fixed outputs are not stateful backend validation |
| Human voice calls | Historical real-integration run, owner Version 2/Version 3 tests and ten reviewed Version 5 calls, including failures | qa-results.md; final-owner-checklist.md | Current Version 6 acceptance remains open. Historical success is not proof of the changed closing/amount/time behavior |

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

## Human voice acceptance checklist

Against released service 17 and live Version 6, follow the three targeted calls in [final-owner-checklist.md](final-owner-checklist.md): refusal/proactive end, compound clarification/time/agreement/handoff, and repeated asks/final status/failed close. Record run IDs and inspect audio plus stored activity. MC correction and interruption can be a fourth short spot check. Earlier coverage remains useful for unchanged behavior. Real email requires owner authorization. Keep sends off and calls synthetic. No new booking is needed.

Recorded outcomes must distinguish observation from inference. A saved reservation is not proof a handoff was spoken. An emailed code to the shared inbox is not carrier identity. An end report does not recreate absent notes. Call-start-to-spoken-offer timing and capacity remain unproven.

## Review and release

Preserve historical failures and setup errors. Reconcile case IDs, versions, fixture shapes, run IDs and denominators before presentation. A fresh service or prompt change requires the relevant regression layer, not an inflated combined test count. Build 20's current read-only visual evidence is in the release record; Build 18 remains historical. Current-version human voice acceptance remains an owner step, not an automatic test result.

Frontend evidence: 39 tests, lint 0 errors / 3 existing warnings, production build then typecheck, and zero production dependency vulnerabilities in a clean Node 22 container. Build precedes typecheck because Next generates image declarations. All 77 current App archive files match the checkout. Published Build 20 overview, queue, bookings, calls, demand and both detail panels were checked at 1280x900, including Real/Test switching, disabled Confirm and the historical PENDING receipt. No Confirm, Decline or Reconcile was clicked. Receipt recovery and error recovery remain component-tested.

Historical full-suite result: 18/22 cases passed all three runs (58/66); failures remain in their original evidence. The subsequent fixed Version 4 passed 44/44. Final Version 5 passed all 23 cases twice (46/46) and was published with owner approval. These model grades do not replace the owner voice checklist.
