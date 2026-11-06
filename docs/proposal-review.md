# Independent review and release gates

The submission source is on `main`. Review used the assignment PDF, source, recorded calls and offline reproductions to look for failures. The operating workspace is [Carrier Sales](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview). [Readiness](readiness.md) identifies the actual deployment state and separates current checks from historical evidence.

## Defects found and repaired

The first expanded implementation passed 507 service tests and 56 App tests, yet independent review reproduced additional safety defects. The repairs below now have regression coverage. Passing a suite was useful evidence, not proof of completeness.

| Failure demonstrated | Repair and evidence |
| --- | --- |
| Accepted freight changed after the quote | Store operating facts, including ZIPs, and compare at acceptance and rep preflight. Material changes require a fresh pitch. `test_selling.py` and `test_rep_actions.py` exercise changed lane, equipment, pickup and dispatch ZIP. |
| A TMS city sentence could disclose a private amount | Restrict locations, commodity and note clauses before voice exposure. Unknown prose and contradictory or incomplete freight become `shipment_review_required`. Reviewers independently retested a spelled-out private amount in a location. The historical feed check found 42/50 then-open loads usable and eight requiring review. |
| Same-MC re-verification failed but retained freight access | Every explicit authority recheck suspends eligibility before the external request. A late answer must match the current lookup. HTTP tests hold a lookup in flight and fail it. |
| A final rejected amount replayed a final offer indefinitely | Native `after_final_offer` distinguishes a fresh response from a transport retry. A final refusal ends the negotiation without a fourth round. Identical transport retries remain stable. |
| A rising posted rate increased a repeated quote above an earlier ask | Stable shipment facts retain the last spoken quote, bounded by the current cap. Both repeat-search and no-search paths have regressions. New shipment terms clear their prior per-load ask history. |
| The first three candidates could conceal a valid fourth | Detail reads continue in batches within the voice deadline. A held load is removed before a counter can consume a round. Unsafe freight gets an operations-review outcome. |
| Booking status was trusted without a valid timestamp | A matched reference and status also require a valid timestamp. Missing or malformed receipt fields produce UNKNOWN. Original bytes are stored in restricted Twin when persistence succeeds, with no automatic resend. |
| A durable hold without a completed source-call agreement could be sent | Confirm requires the matching finalized agreement and trusted identity. Interrupted holds remain visible for follow-up and release. Tests reproduce a reservation write followed by failure, hangup and a refused Confirm with zero TMS writes. |
| Shared demo contact and broad App role could authorize a send | Live booking startup requires an explicit real cohort and enrolled contact roster. Per-reservation trust is checked again. App mutations require an exact platform-authenticated subject assignment. Viewer and forged-body tests exercise the boundary. |
| Forwarded-host headers could control login redirects | Production App origin is explicitly configured. Cookie-bearing writes require the exact configured or allowlisted Origin. Tests include hostile forwarding headers and the HappyRobot iframe origin. |
| New call IDs could evade the per-call email budget | Recipient and total delivery budgets apply across sessions in one process. Fake-clock tests cover shared addresses, failures and expiry. A shared provider limit remains required before scale-out. |
| Open calls were labeled as lost demand | Only evidenced ended calls enter lost-demand counts. Ongoing calls and missing end evidence are separate. Historical call links require known native provenance. |
| Module and nested-function complexity escaped a green test suite | `make check` now enforces 300-line modules, 50-line functions and Radon A/B complexity for every AST function and class. Gate regressions cover nested closures, methods and classes. |


## Negotiation review

Human calls exposed a fixed concession ladder that rewarded different inflated requests. The current service uses bounded reciprocal movement and persistent carrier/load memory. Extreme and moderate descending probes no longer force a climb toward the cap. Separate clients share the same budget, while each call still requires verification and obeys its global round limit.

Independent review of `cc84d6b` found two quote-retraction defects during implementation: a lower cap observed during search was not persisted, and another call's old quote could override the retraction. Both were repaired with regressions. The final review found no remaining local blockers and independently passed 92 focused negotiation, memory and selling tests. [Exact scenarios and limits](negotiation-review.md) retain the result and the conservative cross-row write boundary.

## Validation

The current service passed 591 tests with 98.1% business-rule branch coverage, strict typing, lint and size/complexity gates. The App passed 65 tests, lint, typecheck and production build under Node 22. `make review` opened the authenticated App; Confirm sent one request to a TCP simulator and displayed FAKE0001/PENDING. These local checks used no real booking inventory.

Historical capacity measurements exposed timeouts before fresh-read batching. The new memory then regressed twelve-call opening-acceptance workloads. Review found a safe redundant-write optimization and added ten regressions. [Current before/after capacity evidence](reciprocal-capacity.md) shows all three workloads completing twelve agreements with no unfinished claims. The deadline and provider pacing are unchanged. The fixtures do not establish live peak or heavy negotiation capacity.

## Voice evidence

Original failures remain visible. Version 15 retained 71/74 under its original criteria, including E6's missing thanks inside the close message. Later criteria separate that checkpoint from the built-in voice farewell. Versions 16 through 18 exposed ceiling-probe, exit-priority, final-rate and missing-time-source defects. Version 19 contains the targeted repairs.

Final raw native grades are 70/74 and 73/74, with 10/10 focused consent and exit checks. Manual inspection found four judge interpretation issues and one genuine premature close during contradictory amount clarification. The latter can lose a valid caller opportunity, but does not authorize an incorrect booking. It remains a release limitation. [Readiness](readiness.md#native-conversation-evidence) links raw grades, exact traces and actual speech separately.

## Completed release checks and owner handoff

The final graph, fixed disclosure, prompt and seven bindings were read back. Version 19 completed native checks, a full diagnostic voice agreement on service `9d051ba` and a Production routing/exit smoke after publication. Controlled twelve-call workloads passed within their documented scope. The App and local Confirm path are validated separately, with hosted sends disabled.

The owner still records the genuine human call and five-minute video, reviews the final package and submits through the portal. Representative arrival rates, accents, noise and heavy negotiation contention require pilot acceptance; the synthetic tests do not establish those claims. The known R1 early-close limitation remains visible rather than described as repaired.

## History

Version 8 and App Build 24 remain rollback references. Source `15ce2b6` is retained as `oldmain` and local tag `baseline-v8`. The dated 49-call sample contained 36 verified calls, 29 matches and 19 reservations, dominated by one repeated MC. That sample informed the report; it is not a fixed current denominator or representative market study.
