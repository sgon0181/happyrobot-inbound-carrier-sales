# Independent review and remaining release gates

This proposal was built in an isolated branch. Main, its submission ZIP, the published Version 8 workflow and service release 17 remain the historical baseline. The candidate has not been promoted. The independent reviewers used the original five-page assignment PDF, source, genuine call evidence and offline reproductions. They were asked to find failures rather than validate the author's design.

The first implementation was pinned as `4f6bd51`. It passed 507 service tests and 56 App tests, yet the second review reproduced additional safety defects. Passing those suites was insufficient. The table records the repairs and the regression tests that now exercise them. Final source acceptance is a separate review of the resulting commit.

| Failure demonstrated | Proposal repair and evidence |
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

## Capacity evidence has a boundary

The [pilot guide](proposal.md) retains both successful and failed measurements. Removing redundant initial verification reads improved one isolated fifteen-request authority burst from one eligible result to fifteen, using the actual configured Twin pacer. A separate unpaced test checks twelve concurrent journeys and duplicate rep approvals. Neither establishes simultaneous voice capacity.

The independent paced full-flow runs exposed negotiation timeouts and partial durable holds. Those failed measurements remain documented. The hold repair prevents unsafe submission and overstated conversion after a timeout. It does not increase the provider quota or establish that a larger burst finishes within the voice deadline.

## Voice candidate evidence

The Version 9 native checkpoint run passed 71 of 73 cases, including all fourteen newly added cases. Two historical expectations conflict with the intended new interaction: asking two missing details together, and placing a spoken recap after the private close action. The report keeps their original grades. An earlier corrected-amount failure remains recorded alongside the final four successful reruns.

A complete mocked replay still invented times when its load fixture omitted the authoritative display labels. This remains a model failure and the candidate remains unpublished. The actual service checks both timestamps before a found response and produces the display labels deterministically. An HTTP regression verifies every returned load has both labels and that missing timestamps cannot produce a found load. This reduces exposure to the observed bad fixture but does not establish that the voice model is hallucination-free. The full replay also ended through idle timeout despite the native tool's end-after-execution setting. Reliable audible recap and call termination remain acceptance gates. A new human voice acceptance test is still needed. The retained [Version 9 native evidence](../happyrobot/qa-proposal.json) retains the root hash, exact bindings, checkpoints and failed full replay.

### Version 10 ending repair

The [Version 10 prompt](../happyrobot/prompt-proposal-v10.md) and [tool bindings](../happyrobot/proposal-tool-bindings-v10.json) are the latest proposal candidate. This separate unpublished fork explicitly ends the conversation after the caller-facing close message and its tool result. The automatic tool-ending toggle is off, with [retained UI state](../happyrobot/v10-ending-state.txt) and a [screenshot](../happyrobot/v10-explicit-ending.jpg).

The [two targeted full mocked replays](../happyrobot/qa-proposal-v10.json) both recapped the exact load, rate, pending rep status and goodbye, then invoked the built-in ending two seconds after close_call without another caller turn. They finished in 35 and 38 seconds. Both safely omitted unsupported timestamps in the unchanged incomplete fixture. One repeated the initial MC question, which remains visible in its transcript.

Each native audit graded five passed, one failed and one not applicable. The failed historical criterion requests date displays absent from that fixture. Its failed grade remains unchanged. The 71/73 checkpoint result belongs only to Version 9. Version 10 has two targeted mocked acceptance passes, no full-matrix result and no real audio acceptance. Its safe omissions do not erase the older time hallucination or prove model immunity. Before promotion, rerun the focused refusal and amount-correction cases, the full matrix, and a normal complete-display voice call with interruptions and real hangup verification.

## Before promotion

- Keep the native candidate unpublished until its exact prompt, tool schema and HTTP binding match the reviewed source. Preserve failed checkpoints with successful reruns in the candidate QA artifact.
- Create an isolated native App/service deployment with its canonical origin, assigned rep subjects and enrolled carrier contacts. Verify a fresh call and an actual receipt there. Keep synthetic trials out of the real submission queue.
- Agree arrival timing and tool budgets with the customer, then measure concurrent voice calls against real provider quotas. Shared delivery admission, production alert routing and retention policies are pilot gates.
- Record the owner's narration and new human voice test, then package the exact approved source. The [five-minute cue sheet](proposal-demo.md) is a rehearsal guide, with the recorded Version 8 call explicitly identified. No final owner recording or portal submission is claimed.

The independent browser review exercised the assigned rep's Confirm against the local TCP simulator, observed one PENDING receipt, and replayed a stale version without another send. It checked all five menus at 390, 768 and 1280 pixels without horizontal overflow. The actual 49-call inventory reconciled to 36 verified calls, 29 matched and 19 reservations, with 18 agreements from one MC and a $50 median movement above opening. These are development trials across versions, not a representative business outcome study.
