# Negotiation memory capacity repair

The new shared-memory write exposed a regression in the existing controlled twelve-call workload. All callers accepted their opening offers. The first reciprocal implementation inserted one negotiation row per acceptance before recording the call claim, reservation and final call agreement. At the adapter's chosen four SQL statements per second, those extra writes pushed requests past the unchanged twelve-second voice deadline.

The harness stops at its first error without a final webhook. Its failures therefore retain unfinished claims rather than hiding them through cleanup or a later retry. No TMS booking command is issued in this workload. Existing Confirm guards refuse unfinished agreements.

## Measured before and after

| Workload | Before: agreements / unfinished claims | After: agreements / unfinished claims | After negotiation p95 |
| --- | --- | --- | --- |
| 12 simultaneous, no think time | 5 / 7 | 12 / 0 | 10.57 seconds |
| 12 arrivals 1.5 seconds apart, 3 seconds between tools | 11 / 1 | 12 / 0 | 9.33 seconds |
| Same arrivals, 500 historical calls, 200 released bookings and dashboard polling | 8 / 4 | 12 / 0 | 11.34 seconds |

Every before and after run recorded zero TMS booking sends. All after runs finalized twelve source-call agreements and twelve new durable holds. The history run's 212 booking rows include 200 preexisting released records, not 212 new reservations. The longest measured after-run snapshot was 13.66 seconds, within the App's twenty-second operations deadline.

[Raw measurements and source hashes](../evidence/reciprocal-negotiation/capacity.json) preserve both failures and successes. The final file differs from the initial after-run source only in a comment explaining the decision point; executable statements are identical. These are single-run local observations using fixtures and loopback TCP, not a promise of twelve concurrent production voice calls. The after tests exercise opening acceptance; heavy multi-round contention still needs representative measurements.

## Narrow repair and concurrency boundary

When a fresh Twin read finds no negotiation record, the call has used zero rounds, and the carrier accepts the exact current opening, there is no shared concession or price change to persist. That decision can return without inserting a row. The fresh read remains mandatory. Existing rows still use compare-and-set, including replies that leave the row unchanged. Lower accepted amounts, concessions, repriced quotes, prior rounds and replacement shipment records still persist normally.

The decision is made at the fresh absent-row read. Another simultaneous call may record a lower amount afterward. The fast path leaves that later record intact; it does not claim that the latest lower ask always wins before reservation. Booking ownership still uses its own compare-and-set, so only one competing call can reserve the load. That separate decision and reservation boundary already existed.

Ten focused regression cases cover the mandatory shared read, exact opening acceptance, lower accepted prices, an existing unchanged row, repricing, rounds spent on another load, material shipment changes, concurrent first counters, concurrent lower acceptances, already-present lower memory and competing reservations. Combined with existing memory checks, 28 focused tests pass. Full `make check` passes 591 tests, strict types, lint and size/complexity gates, with 98.1% business-rule branch coverage. Production Python count is 3,868 physical lines.

The repair changes no SQL pacing, voice deadline, booking authorization or TMS send policy. It must be deployed and rechecked before the measurement is described as the hosted runtime's behavior.
