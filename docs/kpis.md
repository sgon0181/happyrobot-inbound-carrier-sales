# KPI definitions

Scope: only call rows whose stored cohort is real. Synthetic calls stay visible separately. CALL_COHORT is currently synthetic on Fly, so current test calls must not be presented as customer traffic. A deploy check historically stamped real is explicitly excluded.

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

The overview's current work cards count current booking rows in the selected scope: RESERVED, UNKNOWN, ACK_PENDING and CONFIRMED. Historical call results count calls and retain prior reservations after release or load-row reuse. They are intentionally separate sections, not stages of one funnel. Test overview shows its own historical call counts without real business performance or a conversion percentage. All views cover all recorded history; no today-only range is implied.
