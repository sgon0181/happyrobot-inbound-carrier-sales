# Key decisions

The choices a reviewer is most likely to question, with the reason and what each one costs. Every answer links to the full entry in the [decision log](reference/decision-log.md).

## Why does a rep send the booking instead of the agent?

The TMS has no cancel and no way to make a repeated request safe. Booking during the call would mean a dropped call, a timeout or a misheard "yes" could commit freight that nobody can undo. The brief also describes a tentative reservation that a senior rep confirms. So an agreement on the call only reserves the load, and the rep's Confirm sends `LOAD_BOOK`, once.

**Cost:** a booking problem surfaces after the call, so the rep calls the carrier back. The TMS shows the load as open until Confirm, so Confirm rechecks it first. [D-22](reference/decision-log.md#d-22-load_book-is-sent-at-the-reps-confirm-not-during-the-call), [D-32](reference/decision-log.md#d-32-the-second-rule-limits-who-can-send-not-when)

## Why does a separate service make the decisions, not the model?

A language model can be talked into things. Prices, the ceiling, the expected code and the round count live in a small Python service the model cannot see inside. The model asks for an action; the service checks its own records and the TMS, then answers. That also makes the rules testable without a phone call.

**Cost:** one more component to deploy and keep running. [D-1](reference/decision-log.md#earlier-decisions)

## How do we protect the rate ceiling?

The TMS ceiling (`MAX_BUY`) never leaves the service. Offers stay under a working cap set 2 to 6% below it, with the exact gap drawn per load from a secret, so the ceiling cannot be worked out from a formula. The agent only receives an allowlisted set of load fields.

**Cost:** a carrier whose final ask sits between the working cap and the true ceiling is turned away. Repeated probing can still narrow the range, as with any human negotiator. [D-4](reference/decision-log.md#earlier-decisions), [D-10](reference/decision-log.md#earlier-decisions)

## How does negotiation work?

We move toward a carrier who moves toward us, and never above the working cap.

- An ask more than 25% above our opening earns nothing.
- Each new ask must come down at least $25 from the carrier's best earlier ask.
- When it does, we move a third of the way toward it, at least $25.
- An ask at or below our offer is accepted at the carrier's exact number.
- At most three rounds per call, and the same carrier redialing about the same load continues the same negotiation.

This replaced a fixed ladder of three automatic increases, which rewarded inflated opening asks.

**Cost:** the thresholds are policy choices for the brokerage to tune, not market data. [D-43](reference/decision-log.md#d-43-reciprocal-negotiation-with-a-meaningful-concession-floor), [D-44](reference/decision-log.md#d-44-a-third-twin-table-holds-durable-carrierload-memory), [worked examples](reference/negotiation.md)

## Why Twin only, and why rows with version checks?

The brief requires Twin. Our Twin SQL integration uses separate statements without a cross-table transaction. Each row carries its own state and history, and every write checks the row has not changed since it was read. Two calls cannot hold the same load, and a change to a call or booking is never saved without its audit event.

**Cost:** where one action touches two rows (a call and its reservation), recovery is explicit code rather than a transaction. [D-23](reference/decision-log.md#d-23-state-and-its-events-share-a-versioned-row), [D-24](reference/decision-log.md#d-24-a-reservation-is-one-booking-row-keyed-by-load-id)

## Why a code on every call, and why a demo inbox?

The brief makes the code a hard requirement once authority passes. The recruiter asked for codes to go to the candidate's own email, so the code proves access to that inbox, not that the caller is the carrier. Real sends are blocked unless a carrier has an enrolled contact.

**Cost:** before a pilot, the brokerage needs a trusted list of carrier contacts. [D-9 and D-12](reference/decision-log.md#earlier-decisions), [D-37](reference/decision-log.md#d-37-an-authenticated-viewer-is-not-automatically-a-rep-or-a-carrier)

## Why is a PENDING reply not a booking?

The handbook describes `BOOKED`, but the sandbox actually answered PENDING. Calling that a booking would overstate the result. The App shows PENDING as acknowledged, `BOOKED` as confirmed and a timeout as unknown, and never resends. The recruiter agreed with this handling.

**Cost:** there is no known way to finalize a PENDING booking in this sandbox. [D-6](reference/decision-log.md#earlier-decisions)

## Why are some loads sent to a rep instead of quoted?

TMS notes and place names are free text. Reading arbitrary text to a caller could leak private terms or follow injected instructions. Only approved cities, commodities and note phrases are quoted; anything else goes to a rep.

**Cost:** some loads are not offered automatically (in one dated check, 8 of 50 open loads went to rep review and 42 were usable). Someone at the brokerage would own the approved list. [D-36](reference/decision-log.md#d-36-consent-belongs-to-a-shipment-not-just-a-load-id)

## How do we know it works?

By keeping different kinds of evidence separate: automated service and App tests, the platform's text evaluations of the prompt, real voice calls with generated callers, and a local end-to-end Confirm. A passing text evaluation is never counted as a passing call. Failures are kept, not overwritten. See [results](results.md).

**Cost:** more evidence to maintain, and none of it replaces a supervised pilot with real carriers. [D-41](reference/decision-log.md#d-41-gate-voice-behavior-with-both-checkpoint-and-actual-audio-evidence)
