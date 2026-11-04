# KPI definitions

## Recorded demo call overview

The Overview answers three questions for the operations manager. How often do verified calls produce a reservation? Where do calls stop? How far does the carrier payment move from the opening offer?

HappyRobot listed 50 inbound sessions for workflow `01a18119-67a1-79a3-b220-369aa359d4fb` from November 2 through 4, 2026. The retained [session inventory](../ops-app/src/lib/demo-voice-runs.ts) comes from the November 4 export at 14:22 UTC. HappyRobot marked 49 sessions completed and one missed with zero connected seconds. All 49 completed runs matched Twin call IDs across workflow versions. The missed session has no Twin call row and is excluded from the completed sample. The 30 text sessions and service deployment check are outside the cohort. New calls remain available in Desk activity and the Calls page. To extend this dated report, reconcile a fresh inbound inventory before updating its IDs and dates.

| Measure | Calculation | Reconciled result |
|---|---|---|
| Verified calls with a reservation, the business North Star | Distinct calls with a historical reservation and successful email verification divided by all calls with successful verification. Released reservations retain the original agreement. | 19 of 36, 53% rounded |
| Call outcomes | Count calls with a Twin row, verification, a successful load search, and a historical reservation. Each call counts once per stage. Matching records that the service returned freight. | 49 recorded, 36 verified, 29 matched, 19 reserved |
| Where verified calls stopped | Verified calls without a reservation, divided by whether their history contains a successful search. Review the calls to establish the reason. | 7 without a match, 10 matched without an agreement |
| Rate above opening offer | Median of agreed rate minus opening rate, using the first successful search event for the same load on the same call. Both prices and matching agreement and historical reservation IDs must be present. | $50, with recorded pairs on all 19 agreements |

The report reads the first appearance of the agreed load in the full call event history. Seven opening prices came from the older offers map, and twelve from load entries in newer search events. The current offers map changes during negotiation. The payment difference measures price movement and does not establish brokerage margin. The underlying drills link each count to calls and show the two prices for each agreement. These cross-version demonstration results do not estimate current customer performance.

## Desk activity and service diagnostics

The following measures use only call rows whose stored cohort is real. Synthetic calls stay visible separately. CALL_COHORT is currently synthetic on Fly, so current test calls must not be presented as customer traffic. A deploy check historically stamped real is explicitly excluded.

| Display | API field | Definition and limits |
|---|---|---|
| Calls recorded | calls | Number of real Twin call rows. A service request creates a row; after Version 4 rollout a successful end webhook also creates pre-tool calls. Not an answer rate or guarantee every platform run was captured |
| Email code verified | code_passed | Real calls that ever recorded a successful code check. A later MC change does not erase this milestone. The demo proves access to the shared configured inbox, not legal carrier identity |
| Reservations created | handoffs | Real calls with a reserved event in booking history, including a later released reservation. Not proof of words spoken, a completed transfer or current ownership |
| Reservation conversion after email verification (northstar) | northstar | Reservations created divided by code-passed calls, rounded to three decimals; null if denominator is zero. Numerator and denominator are shown alongside the percentage. Small demo samples are not a production conversion estimate |
| Historically approved for submission | rep_confirmed | Reservations that entered SUBMITTING after a rep's approval. Includes later failures. Kept in recording diagnostics, separate from current booking-state cards. Does not prove bytes were sent or that the TMS finalized anything |
| TMS pending | tms_acknowledged | Reservations currently ACK_PENDING, backed by a parsed reference-bearing PENDING receipt. Not a final booking |
| TMS confirmed | tms_confirmed | Reservations currently CONFIRMED from authoritative BOOKED evidence. No live BOOKED receipt has been observed |
| Unknown | unknown | Reservations currently UNKNOWN. A send may have landed; never resend. SUBMITTING becomes UNKNOWN only through the defined reconciliation action after 60 seconds |
| Time to first load match | median_seconds_to_first_offer | Median difference between the first service record and its first successful find_loads event, for real calls with both timestamps. Excludes greeting, initial silence and delivery of spoken details. Secondary service diagnostic, not a voice-experience claim |
| End reports | ends_reported | Real rows with an ended_at timestamp from the workflow callback. That timestamp is receipt time, not the exact hangup time |
| Closing notes | closed_with_summary | Real rows with closed_at and nonblank summary. A close with null or whitespace notes does not count |
| Outcomes | outcomes | Derived call outcome: a reservation takes priority, then explicit service outcome, model close, end callback, or quiet-call fallback. end_not_recorded means 30 quiet minutes, not a proven caller hangup |
| Unmatched demand | turned_away | Real calls whose latest derived outcome is no_match, grouped by the latest stored equipment and states. Earlier search events survive but are not additional demand counts |

## Measurements not available

Call-start-to-first-spoken-offer latency, answer rate, completed spoken handoffs, interruption quality, production capacity, revenue and profit are not measured by these counters. The native variable catalog exposes duration and generic timestamps, but their presence alone does not establish a reliable voice-start clock. Do not subtract duration from webhook receipt to invent an exact start. A supported start event or verified session-start timestamp and spoken-offer timing are needed before adding that KPI.

The API retains historical names for compatibility; display labels above are the intended business meanings. TMS money units are displayed as USD under D-10, not a confirmed currency contract. No carrier payment or concession is described as brokerage revenue or profit.

## Current work versus historical results

Desk activity's current work cards count current booking rows in the selected scope: RESERVED, UNKNOWN, ACK_PENDING and CONFIRMED. Historical call results count calls and retain prior reservations after release or load-row reuse. They are intentionally separate sections, not stages of one funnel. Test desk activity shows its own historical call counts without real business performance or a conversion percentage. Desk activity and the rep queues cover all recorded history in the selected scope.
