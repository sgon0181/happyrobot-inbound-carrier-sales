# Submission candidate: baseline and remaining work

Baseline: `main` at `b0d9cf5`, read on 2026-11-03. Codex is the sole writer; Claude reviews the local commits. This maps the owner's full plan before further implementation. Status describes that baseline, not a claim that a local change is live.

| Plan item | Baseline status | Evidence or remaining work |
|---|---|---|
| Keep production in service/, never merge prototype/e2e | Resolved | Existing main remains the implementation; prototype is reference only |
| Read requirements, decisions, onboarding, compliance, QA and redesign | Resolved | Handover and tracked references read; local base confirmed |
| Greeting and MC request | Resolved in Version 3, voice check open | Opening line exists; do not recreate Version 3 |
| MC readback/correction and carrier-name confirmation | Resolved in Version 3, voice check open | S1, S6, E9, E10; check the owner's Version 3 call |
| Ineligible versus unavailable FMCSA | Resolved | Service statuses and E1/E2 are distinct |
| Acceptance, counters and final numbers through negotiate | Resolved in Version 3, continued regression checks | Corrected tool histories; repeated S5/E6 results retained |
| Clarify vague or uncertain rates | Resolved in Version 3 | E8; never infer a caller's agreement from a range |
| Follow load_gone | Open: E7 | Last 3 checkpoint runs passed 1; do not stack more prompt wording |
| Follow negotiation_failed, professional close without transfer | Resolved in Version 3 checkpoints | E6; human voice acceptance still open |
| Agreement, mocked handoff and clean close | Resolved in checkpoints, voice check open | S5; inspect the owner's Version 3 call and repeat voice checklist |
| No final-booking claims for reservation or PENDING | Resolved in Version 3 checkpoints, regression check open | Keep booking meanings separate in app and materials |
| Correct histories, repetitions, versions, failures and reruns | Resolved, report update open | 22 cases, recorded histories, round-by-round results; never replace failures with the latest pass |
| Greeting, corrections, interruptions and closing in voice | Open: owner | No automated checkpoint proves speech recognition or interruption handling |
| Smallest supported change if E7 remains unstable | Open | Service response and mocked eval before workflow publication |
| Code-delivery success/failure activity | Implemented in b0d9cf5, verification open | Add reconstruction and privacy evidence; retain atomic writes |
| Pitch details and each normalized ask/response/round | Implemented in b0d9cf5, gaps open | Fix string-lane projection; retain every search's criteria |
| Reservation and rep decisions | Resolved | Booking-row events and version-checked rep actions |
| Closing, useful notes, dropped/pre-tool calls | Implemented locally, rollout open | /calls/ended and Version 4 callback; skipped summaries remain explicitly absent |
| Row-only reconstruction and no private fields | Open: R3 verification | Multi-round trace, historical search inputs, marked ceiling and expected-code checks |
| No second DB or logging framework | Resolved | Keep Twin row/event writes |
| Rep carrier name, MC, lane, pickup, delivery, equipment, rates | Open: R4 pieces 1 and 2 | Save an explicit load snapshot per reservation; join carrier name; no historical guessing |
| Negotiation timeline, plain statuses, next action | Partly implemented, open | R3 event projection plus labels and action guidance |
| Visible send mode and disabled Confirm | Open | Expose configuration through the authenticated snapshot; disable UI and retain server refusal |
| Refresh, error recovery, receipt recovery and authentication | Resolved, regression check open | Preserve stable recovery components and all action/version checks |
| Readable tables, correct name, historical not recorded | Open | Essential layout and labels; platform name change and final visual review require approval |
| Reservation, approval, acknowledgement, confirmation, unknown meanings | Resolved in service, presentation open | No final confirmation claimed from PENDING |
| Frontend checks and published visual review | Open | Build/typecheck/tests in node:22; final App publish requires approval |
| Service QA count and coverage | Resolved baseline, rerun per commit | b0d9cf5 reports 414; report actual new totals |
| Reproducible randomized inputs/setups | Open: R5 | Seeded checks, explicitly not calls |
| Conversation checkpoint evidence | Resolved package, refresh open | Record prompt, mocks, repetitions and failures |
| Full simulated conversations and terminal outcomes | Open: R5 | Separate service-driver traces from model conversation evaluation |
| Human voice evidence with exact versions | Open: R5 | Separate actual integrations from simulated or mocked checks |
| Hostile, limit-reset, expired-code, rate, no-match and uncertainty cases | Partly covered, inventory open | Reuse current tests, add only uncovered behavior; no live sends |
| Capacity | Superseded as a required benchmark | Remains unproven; the numeric concurrency target is a recommendation |
| Compliance, build description, email and walkthrough claims | Open: R6 | Recorded versus answered; demo inbox versus carrier identity; bounded secrecy; PENDING versus final; no financial extrapolation |
| KPI definitions | Open: R5 | Define denominator, clock and missing-data behavior; no payment labeled profit |
| Five tailored walkthrough next steps | Open: R6 | Pricing/TMS contract; trusted contacts; capacity/conversation validation; supervised pilot; then telephony/notifications |
| Repo/workflow links, access instructions and owner video | Open: R6 | Final links and instructions locally; invitations, video and submission remain owner actions |
| Optional A: remember lowest valid ask | Analysis only after R1 to R6 | No implementation approval; first resolve corrections, withdrawal, fresh agreement and terms |
| Optional B: reservation/unknown Slack alerts | Analysis only after R1 to R6 | No implementation or messaging approval; no booking path in Slack |
| Optional C: analytics/commercial experiments | Analysis only after R1 to R6 | No implementation approval; data quality before charts or alternate policy |

## Approval boundaries

Local work continues without push or deployment. Ask in chat before push, service deployment, workflow publication, App publication, any Fly secret change, any real booking, reviewer invitations or submission. Batch concrete approval requests after the local candidate is reviewable. `CALL_COHORT` remains synthetic until the owner approves changing it; `LIVE_BOOKING` remains off.

The root untracked assignment PDF is untouched. The tracked PDF under docs/ remains the requirements reference.
