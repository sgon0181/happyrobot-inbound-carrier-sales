# Results

The single place for test counts, scores and measured outcomes. Other documents link here instead of repeating numbers. Each layer answers a different question, so a pass in one is never counted as a pass in another. Limits of the system as a whole are in the [README](../README.md#known-limits).

## North Star and KPIs

**North Star: verified calls that end in a reservation.** Calls that passed the email code and produced a reservation for rep review, divided by all calls that passed the code. It measures whether the desk turns qualified callers into agreements.

The App's Overview shows it live, with the funnel behind it (authority checked, code sent, code verified, load matched, reservation), where verified calls stopped, final-offer exhaustion, call duration and how far agreed rates moved from the opening offer. Funnel stages and exception groups open supporting calls. [Exact formulas](reference/kpis.md).

A dated sample of 49 completed test calls (November 2 to 4) had 36 verified calls, 29 matched and 19 reservations, with a median agreement $50 above the opening offer. 18 of the 19 agreements came from the same test MC, so this shows the KPIs working, not a market conversion rate.

## Automated tests

| Layer | Result | What it shows |
| --- | --- | --- |
| Service and repository tooling | 666 tests pass; 98.2% branch coverage of business rules; strict types, lint and complexity gates pass | Pricing, negotiation, verification, reservations, TMS faults, retries, concurrency, authentication and read-only schema validation, without network calls. Sandbox cases cover environment restrictions, expiry, old records, mismatched calls and one-shot sends |
| App | 68 tests pass; lint, typecheck and production build pass | Views, rep permissions, temporary sandbox eligibility and server routes |
| Local end to end | `make review`: Confirm sends exactly one booking to the TCP stand-in, shows receipt FAKE0001 as PENDING and refuses a stale repeat | The whole Confirm path, with no real TMS or carrier |
| Burst load | Three twelve-call bursts of callers accepting the opening offer each finished 12 of 12 agreements with no stuck claims and no TMS sends, with the adapter paced at four statements per second and the twelve-second voice deadline | This controlled workload only, not production peak capacity |

Evidence: [service tests](../service/tests/), [floor validation](evidence/reciprocal-negotiation/floor-validation.json), [current local and hosted Confirm](../happyrobot/qa-v20-voice.json), [burst results](evidence/reciprocal-negotiation/capacity.json).

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
| Platform text evaluations, current Version 20 | Full sweep: 71 of 74. Both-missing display case: 6 of 6 after the fix. Additional null-pickup/empty-delivery cases: 3 of 4 | All six external tools mocked. One failed callback grade misreads an invitation to call back. Remembered-lane and final-refusal checks each failed once, then passed twice. One extra case warned correctly but omitted the other valid pickup time. Failures remain recorded |
| Actual Version 20 audio, Development | Three calls: protected opening survived caller overlap; verification and lane collection led safely to shipment review; a complete call reserved LD01142 at $3,400 after a $3,600 ask and $3,400 counter against a $3,300 opening | Live FMCSA, demo-inbox verification, TMS reads and Twin writes. The complete call took 141 seconds and verified on its first tool attempt. The earlier lane test needed clearer generated code audio; no booking sent |
| Hosted rep Confirm on the same Version 20 call | LD01142 at $3,400: PENDING reference `2LCUJMMDOHY4I6UV`, persisted as ACK_PENDING. One confirmation and one send event; stale repeat rejected with the row unchanged | Real challenge TMS send through the signed-in hosted App, separate from the earlier call audio and local fixture |
| Actual Version 20 audio, Production | Fixed disclosure, authority lookup, code delivered to the demo inbox, then explicit withdrawal, close and agent hangup | Confirms the public endpoint routes to V20. This routing call did not verify the code or reserve a load |
| Native Version 20 audits | 18 passed, 18 not applicable across four actual calls. Complete reservation call: 8 passed, 1 not applicable | Native automated judgments, separate from text tests and manual audio/timing checks |
| Historical platform text evaluations, Version 19 | Two full runs: 70 of 74 and 73 of 74. Ten focused checks on consent and leaving the call: 10 of 10 | Tool calls and replies against written criteria. Of the five failed grades, manual review found four grading misreadings (for example, spelling "CST" as "C S T") and one real defect, kept as a known limit |
| Real call, generated caller, Version 19 | Verified, negotiated ($6,000 then $4,000 against a $3,675 opening), agreed $3,725 on LD01134, accurate pending-review close; no booking sent | Live FMCSA, email, TMS reads and Twin. Ran before the negotiation floor fix |
| Historical real call, generated caller, Production | AI disclosure, FMCSA authority lookup and a code send, then a correct close and hangup. The code was not verified on this call | That earlier Production call routed to Version 19. The owner's call below completed verification |
| Owner's call after the floor fix, run `6dc95ce1-f7e0-44a3-8394-8408b754527e` | Verified MC 138328; flatbed LD01114, Akron, OH to Cedar Rapids, IA, $1,100 opening. Asked $1,250, offered $1,150; asked $1,175, agreed at exactly $1,175. Pending rep review, no TMS send; 124 seconds | The deployed negotiation rule on a load under $1,250, which the earlier rule could not move on. Decisions read from the [live service record](evidence/reciprocal-negotiation/owner-calls-2026-11-07.json) |
| Owner's call, ineligible carrier, run `2e57f13a-6bae-49d9-ae28-845b08db596b` | MC 132354 refused (registration not active); no code sent; closed by the agent in 21 seconds | The FMCSA gate on a live record |
| Walkthrough recording | Pending | Owner must record and supply the required video |

Current evidence: [Version 20 text evaluations](../happyrobot/qa-v20-checkpoints.json), [Version 20 audio and audits](../happyrobot/qa-v20-voice.json). Previous release: [Version 19 text](../happyrobot/qa-v19-checkpoints.json), [Version 19 audio](../happyrobot/qa-v19-voice.json). Earlier versions' scores and failures are kept in [history](history/README.md); they describe those versions only.

## Version 20 release acceptance

Version 20 is live in Production. It protects the opening, aligns search parameters with the lane gate, uses a shared service URL variable, and enables nine Northstars. The final prompt changes two passages so a missing display-time warning comes before the pitch. [Configuration readback](../happyrobot/tool-bindings-v20.json) identifies the exact prompt hash. Workflow audit sampling is enabled at 100%; prompt-span coverage is not a pass rate. A safe success fixture was saved during drafting, but the later hydrated editor preview displayed `invalid_request` again, for an unconfirmed reason. The actual complete voice run received found loads successfully; the editor preview is not claimed as runtime evidence.

The original draft sweeps and failures remain in the checkpoint file. The final sweep's intermittent remembered-lane and final-refusal failures are not erased by passing follow-ups. A separate missing-delivery case correctly warned the caller but omitted the supplied pickup time once. Repeated amount corrections can still cause an early close. These conversational limits do not authorize a booking, bypass verification or permit a price above the service cap.

Four actual diagnostic audio calls exercised the protected opening, verification, missing lane fields, explicit unrestricted geography, no-match recovery, shipment review, negotiation, reservation, closure and Production routing. The complete call retained lane information supplied with the MC. Manual pauses and generated voices are not an AHT or human-acceptance benchmark. The owner still records the final walkthrough.

After hosted Confirm on November 7, the database contained **81 call rows and 21 current booking rows**: **16 RESERVED, 2 ACK_PENDING and 3 RELEASED**. Overview displays **80 platform calls**; one non-platform diagnostic ID is excluded. It shows **27 reservations from 50 verified calls (54%)**, with **26 of 27** agreements from the most frequent MC. These repeated development calls are not a market benchmark. Funnel agreements count calls; booking states count current load rows.

LD01142 at $3,400 belongs to run `64404ab5-c89a-4a96-bc65-b27d23e1804a` and now has its own TMS acknowledgement. The owner's earlier LD01114 call and historical records remain intact. No import, fabricated call or booking-state relabel was needed. Live carrier booking stays off. A temporary challenge-sandbox permission is scoped to MC 138328 and the [release window](reference/release.md#current-release-state).

Service source `91ad2b7` is deployed with all 33 runtime/policy hashes matching; authenticated health returned TMS reachable. App Build 11 uses an exact 91-file source import. Its native environment repeated all 68 tests, typecheck and production build, with zero lint errors and three existing warnings. The production dependency audit reported no vulnerabilities; the development install still reported low and moderate findings. Exact-source `make review` also demonstrated one TCP fixture send, a PENDING receipt and a refused repeat. These results do not establish broad production capacity or human speech acceptance.

The bootstrap SQL was executed twice in disposable PostgreSQL 16, preserving an existing row. Primary-key rejection, version-checked updates and stale-write rejection passed. The read-only schema checker passed against both that database's metadata and the existing Twin staging schema. No hosted DDL ran.
