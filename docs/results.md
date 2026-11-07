# Results

The single place for test counts, scores and measured outcomes. Other documents link here instead of repeating numbers. Each layer answers a different question, so a pass in one is never counted as a pass in another. Limits of the system as a whole are in the [README](../README.md#known-limits).

## North Star and KPIs

**North Star: verified calls that end in a reservation.** Calls that passed the email code and produced a reservation for rep review, divided by all calls that passed the code. It measures whether the desk turns qualified callers into agreements.

The App's Overview shows it live, with the funnel behind it (authority checked, code sent, code verified, load matched, reservation), where verified calls stopped, final-offer exhaustion, call duration and how far agreed rates moved from the opening offer. Funnel stages and exception groups open supporting calls. [Exact formulas](reference/kpis.md).

A dated sample of 49 completed test calls (November 2 to 4) had 36 verified calls, 29 matched and 19 reservations, with a median agreement $50 above the opening offer. 18 of the 19 agreements came from the same test MC, so this shows the KPIs working, not a market conversion rate.

## Automated tests

| Layer | Result | What it shows |
| --- | --- | --- |
| Service | 615 tests pass; 98.1% branch coverage of business rules; strict types, lint and complexity gates pass | Pricing, negotiation, verification, reservations, TMS faults, retries, concurrency and authentication, without network calls |
| App | 65 tests pass; lint, typecheck and production build pass | Views, rep permissions and server routes |
| Local end to end | `make review`: Confirm sends exactly one booking to the TCP stand-in, shows receipt FAKE0001 as PENDING and refuses a stale repeat | The whole Confirm path, with no real TMS or carrier |
| Burst load | Three twelve-call bursts of callers accepting the opening offer each finished 12 of 12 agreements with no stuck claims and no TMS sends, at Twin's four statements per second and the twelve-second voice deadline | This controlled workload only, not production peak capacity |

Evidence: [service tests](../service/tests/), [floor validation](evidence/reciprocal-negotiation/floor-validation.json), [local Confirm](evidence/release-2026-11-07/local-review.json), [burst results](evidence/reciprocal-negotiation/capacity.json).

## Negotiation scenarios

Opening $4,600, working cap $5,000, run against the deployed rule. [All scenarios](evidence/reciprocal-negotiation/scenarios.json), [policy and more examples](reference/negotiation.md).

| Carrier asks | Our replies | Result |
| --- | --- | --- |
| $15,000, $14,000, $13,000 | $4,600, $4,600, final $4,600 | Distant asks earn nothing |
| $6,000, $5,500, $5,200 | $4,600, $4,725, final $4,800 | Movement starts once the ask comes into range |
| $5,000, $4,900, $4,800 | $4,725, $4,775, agree $4,800 | Moving together closes the deal |
| $5,000, $5,100, $5,200 | $4,725, $4,725, final $4,725 | Raising the ask earns nothing more |
| $5,000, $4,999, $4,998 | $4,725, $4,725, final $4,725 | Token moves earn nothing more |
| $15,000, $5,000, $4,900 | $4,600, $4,725, final $4,775 | An extreme anchor does not inflate later concessions |

## Voice

| Layer | Result | What it shows |
| --- | --- | --- |
| Platform text evaluations, live Version 19 | Two full runs: 70 of 74 and 73 of 74. Ten focused checks on consent and leaving the call: 10 of 10 | Tool calls and replies against written criteria. Of the five failed grades, manual review found four grading misreadings (for example, spelling "CST" as "C S T") and one real defect, kept as a known limit |
| Real call, generated caller, Version 19 | Verified, negotiated ($6,000 then $4,000 against a $3,675 opening), agreed $3,725 on LD01134, accurate pending-review close; no booking sent | Live FMCSA, email, TMS reads and Twin. Ran before the negotiation floor fix |
| Real call, generated caller, Production | AI disclosure, FMCSA authority lookup and a code send, then a correct close and hangup. The code was not verified on this call | The Production web call routes to Version 19. The owner's call below completed verification |
| Owner's call after the floor fix, run `6dc95ce1-f7e0-44a3-8394-8408b754527e` | Verified MC 138328; flatbed LD01114, Akron, OH to Cedar Rapids, IA, $1,100 opening. Asked $1,250, offered $1,150; asked $1,175, agreed at exactly $1,175. Pending rep review, no TMS send; 124 seconds | The deployed negotiation rule on a load under $1,250, which the earlier rule could not move on. Decisions read from the [live service record](evidence/reciprocal-negotiation/owner-calls-2026-11-07.json) |
| Owner's call, ineligible carrier, run `2e57f13a-6bae-49d9-ae28-845b08db596b` | MC 132354 refused (registration not active); no code sent; closed by the agent in 21 seconds | The FMCSA gate on a live record |
| Walkthrough recording | Pending | Recorded for the video |

Evidence: [text evaluations](../happyrobot/qa-v19-checkpoints.json), [voice runs](../happyrobot/qa-v19-voice.json). Earlier versions' scores and failures are kept in [history](history/README.md); they describe those versions only.
