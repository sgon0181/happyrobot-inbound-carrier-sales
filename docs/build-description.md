# Inbound Carrier Sales: business and IT build description

The current proposal uses voice Version 15 in isolated development, a Python service and one populated HappyRobot Apps workspace backed by Twin. A carrier can be qualified, matched to freight and reach a recorded rate agreement while other calls arrive. A designated senior rep reviews the originating call and controls any TMS submission. Main, the original submission ZIP and the published Version 8/Build 24 baseline are preserved. [Current evidence, configuration and deployment](readiness.md) identify exactly what was tested.

## Customer problem and scope

The brokerage wants fewer missed opportunities, consistent rate decisions and an audit trail that a rep can use without opening platform logs. The proof of concept automates qualification, matching and negotiation, then leaves the final commitment with the rep. It demonstrates bounded concurrent conversations and traceable decisions. It does not yet measure missed-call reduction, staffing savings, profit or production peak capacity.

1. **Verify the caller.** Check FMCSA operating authority, confirm the carrier name and verify an emailed code before discussing freight. An unavailable authority lookup is not an ineligible carrier. The approved demo inbox proves access to that inbox; production needs independently enrolled carrier contacts.
2. **Match the shipment.** Ask only for missing equipment and lane preferences. Read the TMS, validate the operating fields and quote approved data. Unrecognized instructions, contradictory conditions or incomplete freight require manual review.
3. **Negotiate consistently.** The service sets prices within the private ceiling and allows at most three counter rounds across the call. Relative or corrected amounts need a complete total and appropriate readback. Duplicate or delayed requests cannot buy another concession. A final refusal ends without handoff.
4. **Record an agreement.** Save the rate, carrier, load and shipment facts in Twin. The agent speaks the exact approved agreement and a mocked handoff for senior-rep confirmation. This is an internal reservation, not a final TMS booking.
5. **Review and submit.** The rep opens the reservation with its originating call, prices, shipment and event timeline. Submission rechecks authorization, trusted contact proof, finalized consent, load availability, material shipment facts and the current ceiling. A stale rep action cannot send twice. Imported historical records remain view-only.

## Business visibility

Reservations opens all recorded agreements by default. Awaiting rep is a filter within the same workspace. Overview follows authority, code delivery, verification, matching and reservation, with counts linked to their calls. Active calls contribute stage progress but are kept out of ended-call loss groups. Demand distinguishes an empty search from never reaching search. Bookings separates acknowledgement, final confirmation and uncertain sends.

Opening-to-agreed price movement measures payment concessions, not broker profit. The historical 49 completed-call sample contained 36 email-verified calls, 29 matches and 19 reservations, with a $50 median movement above opening. Eighteen agreements belonged to one MC. Those observations helped identify pilot questions; they are not the current dashboard's fixed denominator or representative market results. The combined workspace includes imported history and newer development calls.

The recording link is constructed only from trusted native workflow provenance or known historical run inventory. Local fixture IDs do not get invented recordings. Platform permissions still govern playback. Twin history is evidence of service decisions, not a substitute for what was actually spoken.

## Safety and transaction boundaries

The model talks; the service decides. Authority, OTP, price bounds, round counts, reservations and rep permissions are enforced independently of prompt compliance. Raw private ceilings and expected codes are excluded from the voice payload. A load-specific cap reduces simple inversion; this does not prove offers reveal no indirect pricing information.

Material shipment changes require a new pitch and agreement. A hold whose write succeeded but whose agreement did not finish cannot be submitted. The rep can release it and follow up. Both open-work and historical views preserve the difference.

The TMS has no supported cancellation or idempotency key. Confirm sends once after a version-checked transition. Ambiguous transport becomes UNKNOWN and is never blindly resent. A matching reference, status and valid timestamp are required for a definitive receipt. PENDING means acknowledged; only an authoritative BOOKED receipt becomes confirmed. Luke accepted this separation. Original bytes remain in restricted Twin when saved, while safe receipt identifiers and digests support browser recovery.

App users are verified through HappyRobot's API. The native response's user `id` is normalized into the internal subject and matched to an explicit rep assignment. Missing, malformed or conflicting identities are denied. Body-supplied names and decoded token claims never authorize an action. Production writes also require the exact configured origin. Keys remain server-side.

## Measured evidence

- **Actual voice:** Version 15 completed three overlapping WebRTC conversations through real authority checks, approved demo email, safe TMS reads and isolated Twin writes. Scenarios were agreement, corrected-price decline and final-offer refusal. All closed through the agent; no TMS booking was sent. The three-way overlap was 176.78 seconds. Callers were generated diagnostics, so human accent/noise and subjective naturalness still need the owner's new call.
- **Native text:** 71 passed and three failed out of 74 locked checkpoints. Raw failures remain visible. Their grading-boundary limitations are documented; real audio does not overwrite those scores. Earlier failed prompts and caller-harness errors are retained.
- **Service and App:** 563 service tests, 97.9% business-rule branch coverage, strict types, lint and enforced size/complexity checks. The App passes 65 tests, lint, production build and typecheck, including the actual native identity response contract.
- **Controlled pressure:** The original paced twelve-call workload exposed timeouts. Fresh-read batching preserves the four-statement-per-second budget, database freshness and twelve-second voice deadline. Both controlled twelve-call patterns then completed twelve agreements without unfinished claims. A separate test included 500 historical calls, 200 released bookings and dashboard polling. These use fixtures and loopback TCP, not a production capacity benchmark.
- **Rep action:** The disposable browser exercise produced one simulated PENDING receipt, then refused a stale replay and a viewer action. The native hosting acceptance and final source identity are separately recorded in [readiness](readiness.md).

## Operation and deployment

| Component | Owner and responsibility |
| --- | --- |
| HappyRobot voice workflow | Conversation, native tools, mocked transfer and end report |
| Python 3.12 service on Fly.io | Rules, authority, email, TCP TMS adapter, Twin events and rep actions |
| HappyRobot Twin | Versioned call and booking rows with histories |
| HappyRobot Apps | Authenticated unified desk, metrics and assigned-rep actions |

After one-time native-resource and secret setup, `make deploy APP=<isolated-app> APP_URL=<native-app-url>` builds and deploys the container, checks authenticated service health and TMS reachability, then opens the App. The exact isolated command was exercised. `make review` instead builds and opens a disposable local simulator with no customer credentials or external business writes.

Point reads batch at their scheduled SQL slot without caching mutable state. Snapshot reads paginate, reject truncated replies and fail closed at their twenty-page bound. The App allows twenty seconds for operations snapshots and suppresses overlapping refreshes. History retention, cross-table non-atomicity, real provider quotas, shared delivery throttling before multi-instance scale, alert ownership and telephony answer/hold telemetry remain explicit pilot constraints.

A staffed pilot should enroll trusted contacts, assign reps, agree arrival patterns and compare matched shifts on missed calls, rep effort and reviewed agreements. The [five-minute owner script](proposal-demo.md) pairs a new human call with its exact reservation and keeps simulated receipts and QA layers clearly identified.
