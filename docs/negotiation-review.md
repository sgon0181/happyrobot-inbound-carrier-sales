# Reciprocal negotiation review

Service correction `8ccbf0a`, based on `26c17ed`, deployed with owner approval on November 7, 2026. [Deployment checks](evidence/reciprocal-negotiation/service-deployment-2026-11-07.json) verify the runtime and guarded settings. Version 19 remains unchanged and its recorded voice evidence uses the prior rule. [Readiness](readiness.md) separates local validation from the hosted release and retains earlier failures.

## Business policy

The service, not the voice model, decides money. We move toward a carrier who moves toward us, in steps of at least $25 while room remains, never above our private limit. Under `reciprocal-v2`:

1. An ask at or below our standing offer is accepted at the caller's exact amount.
2. An ask more than 25% above the opening earns no concession. Reach stays tied to the opening even as our offer moves.
3. After the first ask, the carrier must improve their best prior ask by at least $25. Equal, rising and token asks hold.
4. Move one third of the gap from our offer to the lower of the ask and private cap, rounded down to $25, with a $25 minimum. If less than $25 remains below the cap, use only that room. If the ask is at or below this next offer, accept the caller's exact amount; never overpay to satisfy the floor.

A new above-offer ask consumes one round, including a hold. Exact repeated asks do not spend another round. Three rounds is a limit, not a promised route to the cap. Acceptance of the standing offer remains possible after the final counter; explicit final refusal remains terminal. The pricing-v1 opening and working-cap calculation is unchanged; its legacy target array does not control negotiation.

The previous 2% allowance rounded to zero for every opening below $1,250. Half of a $25 carrier improvement also rounded to zero. The correction deliberately allows more movement and a wider reachable band to close those gaps. These are explicit policy choices for brokerage review, not market-derived rates or proof of optimal conversion. The service does not invent fuel, market, capacity or urgency signals.

Every new call negotiation event and shared round-decision event carries `negotiation_policy_version`. It is separate from pricing-v1, so caps and openings do not redraw. Existing rows retain their standing quote, spent rounds, best ask and original event fields. No historical event is relabeled or backfilled.

## Executed scenarios

All figures below use the same offline fixture: opening $4,600, working cap $5,000. These are not new human calls. Machine-readable results are in [scenarios.json](evidence/reciprocal-negotiation/scenarios.json).

| Carrier asks | Service offers or agreement | Result |
|---|---|---|
| $15,000, $14,000, $13,000 | $4,600, $4,600, final $4,600 | No concessions for distant asks |
| $6,000, $5,500, $5,200 | $4,600, $4,725, final $4,800 | Movement begins when a falling ask enters reach |
| $5,000, $4,900, $4,800 | $4,725, $4,775, agree $4,800 | Reciprocal movement closes the deal |
| $5,000, $5,100, $5,200 | $4,725, $4,725, final $4,725 | Raising the demand earns no further increase |
| $5,000, $4,999, $4,998 | $4,725, $4,725, final $4,725 | Token changes earn no further increase |
| $15,000, $5,000, $4,900 | $4,600, $4,725, final $4,775 | An extreme anchor cannot amplify a later concession |

The moderate descending sequence now earns concessions after entering reach. It would be inaccurate to retain the earlier claim that this entire sequence holds. A final counter need not equal the cap. A carrier can still seek the best authorized deal; the policy bounds cost and removes automatic per-round increases, rather than making negotiation ungameable.

### Floor regression: before and after

The before column was executed against unchanged `26c17ed`. The after column uses the same opening, cap and ask sequence, stopping at agreement. The third ask is unnecessary when the second closes the deal. Both results are retained in [scenarios.json](evidence/reciprocal-negotiation/scenarios.json).

| Opening / cap | Carrier asks | Before | After |
|---|---|---|---|
| $975 / $1,150 | $1,050, $1,025, $1,000 | $975, $975, final $975 | $1,000, agree $1,025 |
| $1,125 / $1,300 | $1,200, $1,175, $1,150 | $1,125, $1,125, final $1,125 | $1,150, agree $1,175 |
| $1,900 / $2,200 | $2,200, $2,100, $2,050 | $1,900, $1,900, final $1,925 | $2,000, $2,025, agree $2,050 |
| $1,900 / $2,200 | $2,050, $2,000, $1,975 | $1,925, $1,950, final $1,950 | $1,950, $1,975, agree $1,975 |

Property-style checks cover openings from $500 to $6,000 in $25 steps, seven cap-room amounts, opening/intermediate/cap offers, reach boundaries and $24 versus $25 improvements. Counters never fall below standing or exceed the cap. Eligible counters with at least $25 room move at least $25; with less room they stop at the cap. Acceptance is intentionally different: it uses the exact ask, including a lower amount or a gap smaller than $25. Escalation and token asks hold; exhausted rounds refuse additional bargaining.

## Memory and failure tests

Executed through the actual Twin adapter with offline storage and HTTP fixtures:

- Redial resumes the standing offer and shared three-round budget after independent verification and search.
- Repeated identical asks across calls do not buy another concession.
- A day of waiting does not reset the budget; a different carrier has separate memory.
- Separate service clients simultaneously negotiating the same carrier/load share CAS rounds 1, 2 and 3.
- Lost call writes and lost acceptance responses preserve the shared decision on retry.
- Contended writes fail closed; no booking is sent.
- Fresh lower caps durably retract quotes, including when another call holds an older quote. Later cap recovery cannot resurrect it.
- Material shipment changes allow a fresh shared negotiation. Price-only changes and workflow versions do not.
- Call-global rounds remain bounded across different loads; existing verification, consent and reservation recovery regressions pass.
- Private caps and negotiation-memory internals do not appear in agent responses.
- Untagged historical memory survives a policy change without relabeling, replay refunds or round resets; only new events carry the new version.

Local floor-correction validation: 604 service tests, 98.1% business-rule branch coverage, 99% combined service coverage and 3,871 production Python physical lines. Ruff, strict mypy and size/complexity gates pass. All 65 App tests plus lint/build/types pass, and fresh browser Confirm sent once to the local TCP simulator with FAKE0001/PENDING. [Readiness](readiness.md) links the validation record. The original `cc84d6b` memory implementation passed 581 tests, 97.5% business-rule branch coverage and 3,850 production Python physical lines. Those historical figures are not the current patch results. No App code changed.

Independent review found and prompted fixes for two quote-retraction defects. Both now have regressions: search must persist a lower quote, and an older call quote must not override the shared decision.

## Voice corrections and subsequent checks

[Prompt draft v16](../happyrobot/prompt-proposal-v16.md) includes:

- Temporary email sending limits explained accurately, with a conservative ten-minute retry instruction.
- Complete MC collection and a correction opportunity for ambiguous matches, rather than treating a partial number as final.
- Immediate respectful exit on goodbye, even while a code or amount confirmation is pending.
- Safe driving wording tied to reading the verification code, not carrier eligibility.
- Shorter load pitch, retaining pickup time, weight, commodity and all operating conditions and fees. Delivery time, piece count and dimensions are available on request.
- Natural counter wording and brief acknowledgment of the caller's stated concern, without invented market evidence, strategy disclosures or invented prices.
- Saved agreement awaiting senior-rep review, not a claimed live transfer or confirmed booking.

Version 16 native and actual voice checks subsequently found issues; later prompts and evidence are tracked in readiness. The original acceptance plan was to verify: email send_limit; split MC 9999 followed by 9999; goodbye during code collection; unsafe driving; repeated fuel-cost request; high and moderate ladders; reachable concession and acceptance; redial; and a full agreement ending with the correct load, rate and pending review. Inspect tool arguments and listen to audio. Static prompt edits do not establish conversational success.

## Fresh recording inventory

A bounded read-only staging/TMS check on November 7 at 09:41 Sydney found two negotiation rows for MC 138328: LD01124 at $2,600 with zero rounds and no best ask, and LD01134 at $3,725 with two rounds and best ask $4,000. Neither has policy metadata. Both rows and their history remain untouched.

| Fresh load | Equipment | Lane | Opening offer |
|---|---|---|---:|
| LD01114 | Flatbed | Akron, OH to Cedar Rapids, IA | $1,100 |
| LD01135 | Reefer | Greenville, SC to Sarasota, FL | $1,200 |
| LD01109 | Flatbed | Buffalo, NY to Tulsa, OK | $2,975 |
| LD01122 | Flatbed | Chattanooga, TN to Reno, NV | $4,000 |
| LD01133 | Reefer | Phoenix, AZ to Flint, MI | $4,550 |
| LD01115 | Flatbed | West Palm Beach, FL to San Francisco, CA | $6,375 |

Each was OPEN, future, unheld, outside protected inventory, safe to quote and without memory for this MC. No dry van passed every filter. LD01114 exercises the small-opening fix; LD01122 carries steel coils on a flatbed and is a clearer freight demonstration. Recheck availability before recording. The [sanitized snapshot](evidence/reciprocal-negotiation/demo-inventory-2026-11-07.json) includes appointments and shipment details, not private caps. No rows were reset and no booking was sent.

## Deployment boundary

The `negotiations` table must exist in the selected Twin environment before deployment. It uses `id` text primary key, `version` integer and `data` JSONB, like existing tables. The table is allowlisted by the adapter and was provisioned and read back in Twin staging. The disposable local reviewer fixture already supports it. Do not add it to the call or booking population in the App.

There is intentionally no automatic expiry. Material shipment changes replace the active shared negotiation; per-call audit events retain the previous history. No historical call rows are rewritten or backfilled. The new policy applies prospectively. Memory is keyed by verified MC, not a uniquely authenticated human dispatcher; the existing demo inbox is still not production carrier identity.

Shared memory is written before the call row, not in a distributed transaction. A later refusal or failed write can consume a concession that was never heard. This conservative behavior prevents retries from refunding money. Simultaneous searches can briefly show a conservative older quote; negotiation rechecks shared state. No new voice-latency or capacity claim is made for the additional Twin reads and writes. Staging latency and conversation acceptance remain release checks.

The owner approved deployment of service source `8ccbf0a`. The service was released without changing the prompt, workflow, App, secrets or hosted booking guard. Authenticated health, TMS reachability and snapshot reads passed; all 32 runtime source/policy files matched. Four pure pricing smoke cases passed on the deployed machine without writes. One fresh Version 19 voice journey remains pending: an in-reach ask, a concession of at least $25, agreement and an accurate pending-review close. Record its run ID in readiness. No Git push or voice call was performed by this deployment.
