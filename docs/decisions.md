# Decisions

Every design decision, why it was made and what it costs. [ARCHITECTURE.md](../ARCHITECTURE.md) describes the result; this file explains the choices. Numbers from the prototype are measured unless marked as estimates. Sources are the two audits in [audits/](audits/) and [lessons from the prototype](lessons-from-prototype.md).

## Decisions made on 2026-11-02

The owner approved D-22 to D-25 and D-29 on 2026-11-02. They follow from a prototype that worked but ran to 4,501 production lines, and the owner's requirement to understand every file handed in.

### D-22: `LOAD_BOOK` is sent at the rep's Confirm, not during the call

Replaces D-8.

- **Why:** the TMS has no cancel and no idempotency key. During a call, that send had to finish inside a 12 second request on a database allowing about 4 statements per second, while the carrier could hang up.
- **Evidence:** a hang-up during booking permanently hid a load, a Twin failure after a real send left no stored reference, and in the model two bookings starting together sent nothing. On LD01094 a load was spent before the caller clearly agreed. The send path took 21 statements, and the code protecting it accounted for much of the size.
- **PDF fit:** the PDF reserves tentatively at agreement and has the senior rep confirm the booking. The handbook describes `LOAD_BOOK` as committing a booking. Luke left the timing to us.
- **Cost:** a booking failure appears after the call, so the rep calls the carrier back. The TMS shows the load `OPEN` until Confirm, so Confirm must re-check it. D-8's reasoning that `PENDING` reads as the tentative stage no longer applies; `PENDING` is now simply what the TMS returned.
- **Would change it:** a reply from Luke, or a rubric, requiring the send during the call.

### D-23: Two tables, with each row holding its own events

Replaces the nine prototype tables.

- **Why:** Twin has no multi-table transactions, but one row updates atomically with a version check. Anything spread across rows can stop halfway.
- **Evidence:** three prototype failures came from this. Reservation spanned claims, a call freeze and a booking row. OTP consumption and call verification were separate writes. State saved first and its audit event afterwards, so an event could be lost. Of 70 statements per call, 13 were audit writes.
- **Book:** *Designing Data-Intensive Applications*: fields updated together can live in one document, which removes the need for multi-object transactions (p.287); conditional writes with a version number (p.302).
- **Cost:** events live in JSON instead of their own table. Rows are larger, though a call has about 30 events at most.
- **Rejected:** a same-row outbox with a projected `call_events` table, which both audits proposed. Nothing consumes that table, so it adds flushing, pruning and lag for no gain. The book's outbox (p.507) exists to decouple downstream consumers, and this system has none. Event sourcing (pp.103-104) was rejected for its replay and versioning cost.

### D-24: A reservation is one booking row keyed by load ID

- **Why:** the primary key gives one winner per load in one statement, which is the behaviour already proven on Twin (1 winner of 20 contenders).
- **Replaces:** the prototype's call claim, load claim, call freeze and booking row. Because the reservation is now a single row, an orphaned claim cannot exist, so no reaper or fencing scheme is needed. That removes the cleanup design the audits debated.
- **Cost:** one row per load, so a later attempt on a freed load carries earlier events forward.

### D-25: Five things removed

| Removed | Why it existed | Why it can go | Remaining risk |
|---|---|---|---|
| Transcript-reading consent check | A false yes spent a load forever | A false yes now creates a reservation the rep can decline. It was 155 lines at complexity 29 and 19, and it caused a redundant question on the passing call. | The rep is the safety check. |
| Transcript redaction and collection | Kept spoken codes out of stored transcripts | Twin stores a summary, so there is no raw copy to redact. It was the most complex function in the repo. | Depends on T-8. |
| Receipt journal | Backed up the in-call send | It sat in container storage, and the evidence records it lost after an automatic stop and start. At Confirm the rep sees the result. | If Twin stays down after a send, the receipt survives in the log and on the rep's screen. |
| Cross-call OTP throttle | Limited sends across calls | Per-call limits stay (2 sends, 3 failures), and codes reach only the demo inbox. | A real deployment would need it back. |
| Retry fingerprinting (D-17) | Caught duplicate tool calls | See D-26. | Depends on T-10. |

### D-26: Repeated requests are answered from stored state

Replaces D-17. Each operation checks whether its effect already happened, so a repeat is safe without a fingerprint cache or a time window. The prototype's cache took about two-thirds of each call row. Platform retries were never proven to happen.

### D-27: No background jobs

Stale calls and stuck bookings are detected when read, and a rep resolves them. This removes the sweep loop, its silent failures and every shutdown question it raised.

### D-28: A size budget

Production Python stays at or under 1,500 lines, with the limits in [architecture section 14](../ARCHITECTURE.md#14-quality). The owner must be able to read and defend all of it. Exceeding the budget requires a recorded reason here.

### D-29: Rebuild small on `main`, porting what is proven

- **Why:** both audits judged the sound parts worth keeping, and 423 lines port unchanged. Most of the remainder exists because of D-8 and the multi-table design, so changing those decisions removes it instead of restructuring it.
- **Changes an earlier view:** both audits said refactor, not rewrite, and the Claude audit said to fast-forward `main`. Those verdicts assumed the same design. Two things are new: the design changes above, and the owner's requirement to read every file on a same-day deadline.
- **Not a fresh start:** the TMS findings, spent-load list, prompt, workflow, dashboard and evidence all carry over. `prototype/e2e` stays on the remote as reference and fallback.
- **Cost:** the prototype's live proof does not transfer. The new code needs its own real call, and at least one load.

### D-30: The dashboard reads through the service

The fallback for T-7 is now the design. The Apps gateway to Twin has been failing, and one path keeps every rule in one place. The ops key stays server-side.

## Earlier decisions

| ID | Decision | Status |
|---|---|---|
| D-1 | One Python/FastAPI service | Active |
| D-2 | Twin is the only datastore | Active |
| D-3 | The service sends codes through an email provider | Active. Gmail SMTP proven live. |
| D-4 | Versioned pricing with a keyed gap below the ceiling | Active |
| D-5 | No cached loads; report a TMS outage honestly | Active |
| D-6 | Separate `ACK_PENDING`, `CONFIRMED`, `UNKNOWN`; never resend | Active |
| D-7 | One service instance | Active. Coordination is by version check alone, with no in-process locks. |
| D-8 | Send `LOAD_BOOK` at rate agreement | **Replaced by D-22** |
| D-9 | OTP on every call | Active |
| D-10 | `MAX_BUY` supplies `max_rate`, subject to validation | Active |
| D-11 | No usable ceiling means pricing review | Active |
| D-12 | Codes go to one configured demo inbox | Active |
| D-13 | Record turned-away demand | Active. Derived from call rows, with no table. |
| D-14 | Carrier view in the operations app | Deferred to optional additions |
| D-15 | Northstar is a handoff per verified call | Changed: reserved handoffs per code-passed call |
| D-16 | `run_id` is the only call identity, in a hidden field | Active |
| D-17 | Retries recognized by request fingerprint | **Replaced by D-26** |
| D-18 | Neutral wording on `UNKNOWN`; no Confirm on `UNKNOWN` | Retired. The carrier is gone before any send, and Confirm applies only to `RESERVED`. |
| D-19 | `service/` on `main` is the only production code | Active, with D-29 |
| D-20 | No standalone test bookings | Active |
| D-21 | Real and synthetic calls kept apart | Active |

Each original decision's full reasoning is in [architecture v2.5](https://github.com/sgon0181/happyrobot-inbound-carrier-sales/blob/prototype/e2e/ARCHITECTURE.md#12-decisions-and-open-questions).

## Open checks

| ID | Question | State | If it fails |
|---|---|---|---|
| T-1 | Do Twin version checks and primary keys hold? | Proven on probes and real tables. Confirm on the new tables. | Small Postgres for coordination, justified under PDF p.4 |
| T-2 | What do `PENDING`, currency and bounds mean? | Open. Asked as [Q8](questions.md). | Show the actual status and disclose the assumption |
| T-3 | Can the service deliver codes? | Proven: Gmail SMTP from Fly | |
| T-4 | Does `run_id` arrive outside model arguments? | Proven on the prototype. Confirm on the real workflow. | |
| T-5 | Can the service reach FMCSA? | Proven from Fly `iad`. The local machine gets HTTP 403. | Native HTTP node passes the raw result |
| T-6 | Can the agent end a voice session and speak the handoff? | Proven on the prototype's owner run. One ineligible-call simulation failed to close, so closing remains a QA item. | |
| T-7 | Why does the Apps gateway to Twin fail? | Open, and designed around by D-30 | |
| T-8 | Can a native post-call node produce a summary for the close request? | Not tested in this workspace. Documentation shows AI nodes that accept transcripts. | A deterministic summary from events, as on the prototype |
| T-9 | Should workflow run dumps store full transcripts in Twin natively? | Not tested. They would add spoken codes to Twin. | Transcripts stay on the platform |
| T-10 | Does the platform retry tool calls? | Unknown. D-26 is safe either way. | |
