# Optional improvements after R1 to R6

Analysis only. No optional behavior, Slack integration or pricing policy is implemented by this document. The owner's approval is required before any implementation. The assignment remains the reference: consistent bounded negotiation, reviewable Twin activity, an operational App and documented QA. It does not require lowest-ask memory, Slack or more charts.

The local R1 to R6 candidate is complete for review at 6015242, with remaining rollout, voice, visual and deliverable steps in submission.md. The pressure text simulation's idle timeout is still disclosed. Optional additions must not delay those checks or obscure the difference between a reservation and final TMS confirmation.

| Option | Value | Recommendation | First useful place |
|---|---|---|---|
| A, lowest valid carrier ask | Could avoid offering more than an earlier still-valid ask on the same unchanged shipment | Worth a small policy proposal and offline experiment after acceptance; do not implement a running minimum yet | Pure negotiation policy and version-checked call decision, not prompt-only memory |
| B, Slack alerts | Could reduce how long a rep overlooks a reservation or unknown send | Useful for a supervised pilot if a rep owns the channel; defer for this submission | Notification intent after saved booking transition, separate sender and authenticated App link |
| C, analytics/policy experiments | Review age can guide work; measured concessions/failure reasons may guide a later pricing review | Prefer one actionable queue-age measure if a real backlog appears; otherwise definitions and data quality first | Existing Twin events and authenticated snapshot, without a new database |

## A. Remember the lowest valid ask

The current service does not retain a negotiated running minimum as policy. It accepts an ask at or below the current offer or next target, and can otherwise increase its offer toward a fresh cap. Example: opening 1700, next target 1900, first ask 2000 produces a 1900 counter. A later higher ask can move the next target above 2000. If the caller then accepts that higher counter, the service can pay above the earlier ask while still obeying every current ceiling/round rule. This is a possible commercial inefficiency, not a demonstrated violation of the PDF.

A number is not enough to authorize an agreement. Before adding memory, the owner must decide:

- Valid ask: one explicit positive whole amount, passed through negotiate for a verified call and a particular MC, load and negotiation episode. An MC change invalidates that carrier's remembered quote while preserving the call-wide round budget. Vague ranges, guesses, prices for other loads and invalid money do not qualify.
- Correction: "I meant 2200" should replace the mistaken ask, rather than preserving it as a binding minimum. Withdrawal, misunderstanding or "that price was for another lane" also needs explicit treatment.
- Shipment changes: pickup, delivery, equipment, dimensions, commodity or conditions can invalidate an old ask. The TMS supplies no stable shipment revision ID. Define what constitutes changed terms before using history across fresh reads.
- Authority: the remembered ask should bound a new offer only when valid and compatible with fresh terms. It must not silently accept an old amount after the caller raised or withdrew it. Ask for fresh agreement where needed.
- Fresh bounds: if a changed opening/cap no longer fits the proposed remembered bound, the policy must decide what to say. Do not bypass the current fresh-term checks or conceal a changed deal by clamping numbers.

If approved, keep the decision in core/negotiation.py with explicit inputs, and save any remembered ask/correction alongside the call event inside CallRows.step. Preserve the three-round budget across loads and MC changes, same-ask repeat behavior, one accepted agreement and booking claim recovery. Avoid an extra table, hidden model memory or a second acceptance path.

Verify with examples of higher/lower asks, correction, withdrawal, unchanged/changed terms, duplicates, stale writers, fresh lower cap, exhausted rounds and locked agreement. Add conversation checks for the necessary clarification. Compare the new policy with the existing one on reproducible inputs before changing the policy version. Do not claim savings from generated examples or confuse a quoted ask with consent.

## B. Notify the rep in Slack

The value is an alert that leads to a decision, not another booking interface. The first scope should stay at a new reservation awaiting review and an unknown submission requiring investigation. Include carrier/MC, load, lane, agreed payment, plain status, next action and an authenticated App link. Exclude expected or spoken codes, private ceilings, credentials and raw transcripts. Slack must never offer approval buttons or send LOAD_BOOK.

The saved booking transition is the trigger. Notification delivery cannot decide whether a reservation or send succeeded. A failed Slack request must leave the booking outcome unchanged. Use a stable reservation-event identity (load plus event sequence or claim ID), not the load alone, for repeat handling and define what a duplicate looks like when a delivery acknowledgement is lost. Exactly-once notification delivery is not established by a row flag.

Alerts only on saved UNKNOWN transitions do not cover stuck SUBMITTING rows or receipt_not_saved outcomes until reconciliation records UNKNOWN. A later stale-send detector would need separate approval; do not imply this first alert scope monitors every uncertain send.

A direct send after saving is the smallest best-effort version, but a crash can lose the alert. Durable retry needs an intent stored with the booking event and a separate dispatcher, which reopens D-27's no-background-job choice and consumes Twin's limited statement budget. Do not add that machinery without a concrete response-time need. Native workflow notifications may also miss rep-originated UNKNOWN transitions, so confirm their coverage before choosing them.

For a pilot, first agree who monitors the channel, response expectations, repeat policy and a test channel. Tests should inject failed/slow delivery, duplicate transition handling, delayed/out-of-order delivery, re-reservation of a freed load and acknowledgement loss, with booking results unchanged and no sensitive fields. Any real message requires authorization. No Slack message or configuration change was made during this analysis.

## C. Analytics and commercial experiments

Use existing evidence before adding charts:

| Candidate | Available evidence | Definition needed before implementation |
|---|---|---|
| Time awaiting review | reserved event time and later submitting/declined events | Age of a current reservation, plus time-to-decision for completed review; distinguish missing history and synthetic rows |
| First offer versus agreement | Per-call search pitch offer and saved agreement | Match the same call, MC, load, negotiation episode and unchanged terms; label recorded service offer, not necessarily spoken offer; identify missing historical pitch data |
| Concession per agreed deal | First recorded offer and agreed carrier payment | Agreed minus first offer under a stated cohort; negative amounts possible when caller accepts below opening. Not brokerage profit or revenue |
| Failed negotiations | Sticky failure outcome, asks, rounds and responses | Separate rate rejection, exhausted rounds, unavailable load, service outage, hangup and absent end. Do not infer a reason never recorded |

Four historical real-cohort rows and a few synthetic calls cannot establish conversion, financial impact or a better commercial policy. Queue age could become actionable first, because it identifies work the rep can actually perform. Extra payment charts and alternate pricing policies should wait for sufficient comparable data and agreed assumptions. Any future experiment needs a versioned policy, offline comparison, bounded adversarial tests and explicit approval before live use.

## Decision for this submission

Keep A, B and C as proposals. Finish the reviewed rollout, Version 4 voice checklist, published App visual review, access and owner video first. After that, A deserves a business-policy discussion, B deserves a pilot operations discussion, and C should start only with a measure tied to a decision. No new architecture or external database is justified by these optional ideas alone.
