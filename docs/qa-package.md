# Layered QA package

These layers answer different questions. Generated pricing inputs are not calls, a scripted HTTP journey is not an LLM conversation, and a model's grade is not a proof. All new automated tests and native simulations use fake or locked integrations. No live booking is part of this package.

| Layer | Current evidence | Reproduce or review | Limits |
|---|---|---|---|
| Automated service tests | 438 passed; 1622 statements and 394 branches, all covered; gated 244/244 | make check; service/tests/ | The network guard allows loopback only. Fakes do not prove live capacity or integration contracts |
| Randomized pricing inputs | 20,000 generated loads, seed 7 | test_pricing.py::test_the_rules_hold_across_many_loads | Posted100..12000, ceiling70%..130% of posted; unpriceable inputs are skipped, with more than19000 priced asserted. No model, speech or TMS |
| Randomized negotiation setups | 5,000 generated setups, seed 11 | test_negotiation.py::test_no_rate_above_the_cap_is_ever_offered_or_accepted | Posted500..9000, ceilings600..11000, asks1..20000, up to5 decisions until terminal. Unpriceable setups are skipped; not5000 calls |
| Conversation checkpoints | Historical 22 definitions and three rounds retained; full 22 current Version 4 cases, 66 runs (58 pass, 8 fail), plus six earlier candidate cases 18/18 | happyrobot/qa-v4-full.json, qa-v4-results.json, historical qa-evals.json, e7-candidate.json, e7-results.json, prompt-v4.md | Each checkpoint starts from a scripted history. All 6 actions explicitly locked. Does not run the end callback or prove speech |
| Complete HTTP service journeys | Nine scenarios through real routes and fake integrations | service/tests/test_journeys.py | Includes3 equipment/lane/carrier combinations. A scripted driver supplies user decisions; no LLM, audio or spoken handoff is measured |
| Full model conversations | Two native full-workflow text simulations on Version 4 | happyrobot/simulations.json, standard agreement passed; pressure resisted bypass but ended by idle_timeout | All 7 external actions, including call_ended, must be locked. Fixed outputs do not implement a stateful TMS or code checker |
| Human voice calls | Historical real-integration run and owner's Version2/Version3 tests | qa-results.md, owner voice checklist below | Not repeated by this automated package. Version4 voice acceptance remains an owner step |

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

After reviewed service deployment and Version4 publication, the owner records run IDs and exact versions for: prompt greeting; misheard MC corrected; wrong carrier-name correction; interruption/resumption; clear amount clarification; E7 explanation and consent; agreement/handoff/clean close; failed negotiation with no handoff. Real email requires owner authorization. Keep sends off for hostile or failed-path testing. No new booking is needed to test these voice behaviors.

Recorded outcomes must distinguish observation from inference. A saved reservation is not proof a handoff was spoken. An emailed code to the shared inbox is not carrier identity. An end report does not recreate absent notes. Call-start-to-spoken-offer timing and capacity remain unproven.

## Review and release

Preserve historical failures and setup errors. Reconcile case IDs, versions, fixture shapes, run IDs and denominators before presentation. A fresh service or prompt change requires the relevant regression layer, not an inflated combined test count. Final human voice and published App visual checks remain approval steps, not automatic test results.

Frontend evidence: 13 tests after the reservation-history follow-up. A synthetic static preview checks candidate layout at 1280x900; no authentication, live fetch, receipt persistence or click behavior is inferred from that rendering. Those behaviors have component regression tests and still need the published-App acceptance check.

Latest full-suite result: 18/22 cases pass all 3 repetitions. S6 wrong-name recovery failed once; E1/E2 omitted close_call in all 3 each; S5 omitted its explicit load ID once despite correct negotiate/close and handoff. The raw 58/66 grade is retained. Fixes must be measured in a new batch, not substituted into these results.
