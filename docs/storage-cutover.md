# Entity storage cutover, 1 November 2026

The old aggregate is frozen. Calls, bookings and OTP challenges now have individual
versioned rows. Call and load claims use the existing claims table's primary key.
The runtime excludes the old control row from all entity views and never reads it.
MemoryRepository implements the same row contract for offline tests.

The private backup contains 110 entities. There were zero differences between the
canonical snapshot and projected data. Migration verified every entity, enriched
four active bookings' claims and froze their calls, and preserved the old control
row. Both real receipts, consent evidence, rep decisions and the LD01094 review
flag remained unchanged. Historical authorizations remain evidence only.

A booking acquires call and load claims, freezes its matching verified agreement,
inserts its booking row, persists intent, then sends. An incomplete reservation
stays blocked. A failed booking releases claims only when no intent exists.
Release removes the old call freeze first, its load claim next, and call claim last.
Retries find recorded operations, including failed operations. No send is retried.

OTP consumption commits on its own challenge row before call verification is
promoted. Promotion rechecks the MC, current challenge, eligibility and failure
budget. A crash between those writes leaves the call unverified. Events, rounds,
carriers and other auxiliary records use independent inserts or upserts.
Background collection makes no write when nothing changed.

## Live infrastructure checks

All business records below are labelled synthetic. These tests used no TMS or
email integration. Eight independent call sequences each performed four saves.
They were not eight voice calls.

| Check from Fly | Result | Median | p95 |
| --- | --- | --- | --- |
| Eight contenders for one load | One winner | 26,217.0 ms | 27,099.2 ms |
| Eight transitions on one booking | One winner | 4,882.4 ms | 5,770.5 ms |
| Eight independent call sequences | All eight completed | 17,186.3 ms | 18,065.5 ms |

The independent sequences completed in 18,065.7 ms total, compared with
137,459.8 ms summed across individual sequences. They overlap rather than sharing
a business-state lock. These durations include gateway queueing and failed-claim
cleanup. They do not establish ordinary single-call response latency.

Two earlier probes hit HTTP 429 and remain recorded as failures. SQL starts are
paced at four per second, with at most four in flight, and only explicit 429
rejections receive bounded retries. Arbitrary transport failures do not trigger
SQL retries. No TMS booking is included in that retry helper. A scoped read-only
UNION gets one call, its current challenge and its bookings in one request.

Live submission remains disabled during this storage step. The next step removes
the obsolete run restrictions and introduces off, rehearse and live modes.

Evidence: [cutover](prototype-evidence/candidate-storage-cutover.json),
[contention](prototype-evidence/candidate-storage-contention.json),
[safety readback](prototype-evidence/candidate-storage-invariants.json).
The private backup and failed raw logs stay in ignored secrets paths.
