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

The current service passed 581 tests with 97.5% business-rule branch coverage, strict typing, lint and size/complexity gates. The App passed 65 tests, lint, typecheck and production build under Node 22. `make review` opened the authenticated App; Confirm sent one request to a TCP simulator and displayed FAKE0001/PENDING. These local checks used no real booking inventory.

Historical capacity measurements exposed timeouts before fresh-read batching. Subsequent controlled twelve-call workloads completed twelve agreements at the unchanged SQL pacing and tool deadline. Those runs predate cross-call negotiation memory and are not a latency claim for the updated runtime. [Readiness](readiness.md#concurrency-and-read-budget) links successful and failed measurements.

## Voice evidence

Version 15's original 71/74 text grades remain unchanged, including S5, E6 and TRM. Inspection of E6 confirmed that its caller-facing close message omitted thanks. That finding must not be dismissed as a test mismatch. Any changed definition or rerun is new evidence, with the original grade retained.

Version 16 adds fixed AI disclosure and the reviewed voice corrections. Its repeated checks found a ceiling-probe tool call, omitted CST and vague amount readback. Those real defects block promotion until the corrected successor is retested and accepted in actual audio. Version 15's three overlapping diagnostic audio calls establish only those exact journeys. Earlier Version 9 through Version 13 results, time-display failures and ending repairs remain available in the existing evidence files. None is a substitute for acceptance of the final version.

## Remaining release gates

- Verify the final graph, disclosure, prompt and service bindings; complete native checks and actual voice acceptance on that version.
- Measure the revised service under representative concurrent calls, including the additional shared-memory writes.
- Verify the populated App, native recording access and same-run reservation.
- Keep the owner-selected demo email route and hosted sends disabled. Show Confirm locally and identify any historical sandbox receipt separately.
- Publish the tested workflow to Production, read back the active version and verify the production entry point before recording.
- Record the owner's genuine call and walkthrough, then package the reviewed main commit. The owner submits through the portal.

## History

Version 8 and App Build 24 remain rollback references. Source `15ce2b6` is retained as `oldmain` and local tag `baseline-v8`. The dated 49-call sample contained 36 verified calls, 29 matches and 19 reservations, dominated by one repeated MC. That sample informed the report; it is not a fixed current denominator or representative market study.
