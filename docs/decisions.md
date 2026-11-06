# Decisions

Material design decisions, why they were made and what they cost. The dated baseline choices remain below; D-36 through D-44 document the submission design. [ARCHITECTURE.md](../ARCHITECTURE.md) describes the result, and [readiness](readiness.md) distinguishes deployed evidence from outstanding acceptance checks. Numbers from the prototype are measured unless marked as estimates. Sources are the two audits in [audits/](audits/) and [lessons from the prototype](lessons-from-prototype.md).

## Decisions made on 2026-11-02

The owner approved D-22 to D-25, D-29, D-31 and D-32 on 2026-11-02, and later that day changed D-28 from a cap to a guideline. They follow from a prototype that worked but ran to 4,501 production lines, and the owner's requirement to understand every file handed in.

### D-22: `LOAD_BOOK` is sent at the rep's Confirm, not during the call

Replaces D-8. On November 5 Luke accepted the approach described in the November 3 follow-up, including one submission at rep confirmation and a separate PENDING acknowledgement. No general sandbox finalization behavior was established. [Q8](questions.md)

- **Why:** the TMS has no cancel and no idempotency key. During a call, that send had to finish inside a 12 second request on a database allowing about 4 statements per second, while the carrier could hang up.
- **Evidence:** a hang-up during booking made the load unavailable on the observed token, a Twin failure after a real send left no stored reference, and in the model two bookings starting together sent nothing. On LD01094 a load was spent before the caller clearly agreed. The send path took 21 statements, and the code protecting it accounted for much of the size.
- **PDF fit:** the PDF reserves tentatively at agreement and has the senior rep confirm the booking. The handbook describes `LOAD_BOOK` as committing a booking. Luke left the timing to us.
- **Cost:** a booking failure appears after the call, so the rep calls the carrier back. The TMS shows the load `OPEN` until Confirm, so Confirm must re-check it. D-8's reasoning that `PENDING` reads as the tentative stage no longer applies; `PENDING` is now simply what the TMS returned.
- **Would change it:** a reply from Luke, or a rubric, requiring the send during the call.

### D-23: State and its events share a versioned row

The original call and booking tables replaced nine prototype tables. D-44 adds durable carrier/load negotiations as a third Twin table, using the same row and event boundary.

- **Why:** Twin has no multi-table transactions, but one row updates atomically with a version check. Anything spread across rows can stop halfway.
- **Evidence:** three prototype failures came from this. Reservation spanned claims, a call freeze and a booking row. OTP consumption and call verification were separate writes. State saved first and its audit event afterwards, so an event could be lost. Of 70 statements per call, 13 were audit writes.
- **Book:** *Designing Data-Intensive Applications*: fields updated together can live in one document, which removes the need for multi-object transactions (p.287); conditional writes with a version number (p.302).
- **Cost:** events live in JSON instead of their own table. Rows are larger, and grow with repeated activity. No event-count maximum is proven; row size and retention need pilot measurements.
- **Rejected:** a same-row outbox with a projected `call_events` table, which both audits proposed. Nothing consumes that table, so it adds flushing, pruning and lag for no gain. The book's outbox (p.507) exists to decouple downstream consumers, and this system has none. Event sourcing (pp.103-104) was rejected for its replay and versioning cost.

### D-24: A reservation is one booking row keyed by load ID

- **Why:** the primary key gives one winner per load in one statement, which is the behaviour already proven on Twin (1 winner of 20 contenders).
- **Replaces:** the prototype's multi-table reservation layout. The booking row alone decides the holder, but one agreement per call still crosses the call and booking rows. Review found that the original no-claims argument was wrong. The implementation now uses an ID-bearing accepting claim, resolves it from booking history, and voids a stale claim through the booking row's own version-checked write before repricing. This is explicit recovery, not a multi-row transaction.
- **Cost:** one row per load, so a later attempt on a freed load carries earlier events forward.

### D-25: Five things removed

| Removed | Why it existed | Why it can go | Remaining risk |
|---|---|---|---|
| Transcript-reading consent check | A false yes could trigger a non-cancellable send | A false yes now creates a reservation the rep can decline. It was 155 lines at complexity 29 and 19, and it caused a redundant question on the passing call. | The rep is the safety check. |
| Transcript redaction and collection | Kept spoken codes out of stored transcripts | Twin stores structured activity and optional closing notes, so there is no raw copy to redact. It was the most complex function in the repo. | No verbatim Twin transcript; missing closing notes stay missing. T-8 is optional. |
| Receipt journal | Backed up the in-call send | It sat in container storage, and the evidence records it lost after an automatic stop and start. At Confirm the rep sees the result. | If Twin stays down after a send, the service logs the receipt and returns it to the rep when possible. Logs and browser recovery are not a durable independent journal; process/log retention failure can lose evidence. |
| Cross-call OTP throttle | Limited sends across calls | Removed for the November 2 demo baseline, retaining per-call limits (2 sends, 3 failures). | Reintroduced in the proposal after cross-session inbox abuse review; D-37 specifies its bounded process-local scope. |
| Retry fingerprinting (D-17) | Caught duplicate tool calls | See D-26. | Depends on T-10. |

### D-26: Repeated requests are answered from stored state

Replaces D-17. Each operation checks whether its effect already happened, so a repeat is safe without a fingerprint cache or a time window. The prototype's cache took about two-thirds of each call row. Platform retries were never proven to happen. The current submission retains up to three concession-producing load/ask signatures with their shipment context, so an interleaved retry cannot consume another global round. A later safe standing quote remains binding, and accepting it takes priority over an older signature. Replays report the current global round and final-offer status, so an old request cannot reopen bargaining after the final quote. Changed shipment facts clear those per-load signatures, while the call-wide round limit remains.

### D-27: No background jobs

Stale calls and stuck bookings are detected when read, and a rep resolves them. This removes the sweep loop, its silent failures and every shutdown question it raised.

### D-28: Size is watched, not capped

- **Was:** a hard cap of 1,500 production lines, so the owner could read every line.
- **Changed on 2026-11-02:** line count is a weak measure of quality. The owner now prioritises code that works, passes its tests and is understood at the level of what each part does, over reading every line.
- **What is enforced instead:** the gates in [architecture section 14](../ARCHITECTURE.md#14-quality), which are complexity, strict types, lint, branch coverage, one-way dependencies, and functions and modules kept short.
- **What stays:** every commit reports its production line count, so growth stays visible. Less code is still better when it is equally clear. Slice 1 used 646 lines.

### D-29: Rebuild small on `main`, porting what is proven

- **Why:** both audits judged the sound parts worth keeping. Most of the remainder exists because of D-8 and the multi-table design, so changing those decisions removes it instead of restructuring it.
- **Changes an earlier view:** both audits said refactor, not rewrite, and the Claude audit said to fast-forward `main`. Those verdicts assumed the same design. Two things are new: the design changes above, and the owner's requirement to read every file on a same-day deadline.
- **What carries over is behaviour, not code:** measured against [architecture section 14](../ARCHITECTURE.md#14-quality), none of the prototype's slice 1 code passes as written. No function has type hints, and the files show 115 lint issues and 95 strict type errors. So each piece is rewritten small, with the prototype's tests and recorded TMS replies as the check, and compared with the prototype on the same inputs before it is committed.
- **Not a fresh start:** the TMS findings, spent-load list, prompt, workflow, dashboard and evidence all carry over. `prototype/e2e` stays on the remote as reference.
- **Cost:** the prototype's live proof does not transfer. The new code needs its own real call, and at least one load.

### D-30: The dashboard reads through the service

The fallback for T-7 is now the design. The Apps gateway to Twin has been failing, and one path keeps every rule in one place. The ops key stays server-side.

### D-31: Rep actions carry the version the rep saw

- **Why:** a booking row is keyed by load ID, and a freed load can be reserved again by another call. Without this check, a rep on an out-of-date screen could confirm or release a reservation they never reviewed.
- **How:** the snapshot returns each booking's version. Confirm and decline send it back, and the service refuses if the row has moved on.
- **Cost:** a rep on an out-of-date screen is refused and has to refresh.

### D-32: The second rule limits who can send, not when

- **Why:** the earlier wording, "nothing irreversible happens during a call", did not match the design. A reservation exists before the call ends, nothing makes Confirm wait for it, and the code email is also sent during a call. What protects the TMS is that the voice agent has no route to `LOAD_BOOK`.
- **Cost:** a rep can confirm while the carrier is still on the line. The send runs outside voice cancellation, but the rep still owns the approval and the external outcome may be uncertain.
- **Also changed:** INV-1 now covers what the service returns and accepts, because the service cannot control what the model says.

## Decisions made on 2026-11-03

### D-33: No fallback to the prototype

- **Was:** if slice 4 was not working 4 hours before the upload, submit `prototype/e2e` with its limits disclosed.
- **Changed on 2026-11-03:** the owner chose to finish the rebuild, aiming for working software by 16:00 and recording the demo video that evening.
- **Why:** the owner would rather hand in code they stand behind than a prototype they never reviewed.
- **Cost:** if slice 4 runs late there is no finished fallback, and the owner would bring in Codex to help finish.

## Decisions made on 2026-11-04

### D-34: Voice and App use explicit Central Time displays

- **Why:** owner test calls read UTC clock values without a timezone, while the App displays America/Chicago. A date can change between those displays.
- **How:** the service adds Central Time speech strings to its public allowlist, retaining the original ISO timestamps. Each string names CST or CDT; absent times remain null. The voice reads the supplied display rather than converting a timestamp itself. After Claude's audit, the speech form is "November 7 at 7:36 PM Central (CST)", built portably with no year or padded day/hour.
- **Limits:** this does not validate the TMS source timezone. UTC remains an adapter assumption. The service change must be deployed before publishing the voice draft that depends on these fields; release was not authorized by that local implementation task. The owner later approved release 17 followed by Version 6 publication, now recorded in releases/2026-11-04-v6/README.md.

### D-35: Clarify totals before mutation; make the closing action explicit

- **Why:** Version 5 owner calls turned compound amounts into partial agreements, labeled a first counter final, repeated unchanged offers as new, and reopened farewells.
- **Candidate:** one clear caller-stated total before negotiate, including confirmation of additions or percentages. Ordinary complete number words remain valid. Final status is scoped to this load and amount. Repeated asks still reach the service and retain D-26; unchanged responses are described as unchanged. The acceptance question is one yes/no question about the stated amount, avoiding an ambiguous yes to accept-or-end.
- **Closing:** close_call saves notes, not the voice connection. The candidate records the close, then asks the native voice hangup tool to carry the truthful handoff or refusal and farewell in its final-message field. All eight audited refusal/follow-up/failure branches explicitly use step 6 and _hangup._message. Claude confirmed that this mechanism is supported; 11 subsequent Version 6 timed traces now show proactive endings and final-message content. Audio listening remains limited as recorded below. No new booking path or business rule is introduced. A tested closing-module experiment did not improve the refusal and was removed.
- **Version 7 follow-up:** owner call b4f55923 clarified a broken amount to a 3800 prefix, then added 25 after negotiate. The owner intended 3825. After an actual clarification request, read back the complete total and require an explicit yes before negotiate; a fragment/correction or changed load invalidates it. Clear initial amounts, direct acceptance, repeated asks and same-number service retries remain direct. Do not suggest a calculated example. Version 7 also pitches every supplied operating condition/fee without adding note fees to the service offer. No service, model or orchestration change.
- **Evidence and cost:** 11 Version 6 timed traces have one close and one proactive hangup each, no subsequent caller turn, and stored end records; audio listening is not claimed. Version 7 passes 51 checkpoints twice; two fully mocked multi-turn traces preserve 3825 and notes but do not record final spoken closing. Ambiguous amounts add a confirmation turn. This cannot eliminate every STT segmentation race. See voice-tuning.md.
- **Version 8 follow-up:** recorded Version 7 call b61fba6e submitted 110025 after an explicit No and later 1125 after renewed clarification without readback. Version 8 gives pending confirmation priority, treats No as non-confirmation and requires a fresh affirmative after a corrected total. An eight-case suite scored 16/24 on unchanged Version 7, exposing eight failed executions; final focused 24/24 and full 59-case suite twice 118/118 pass. Two mocked complete replays submitted only 1125 after readback and Yes. The owner reports a successful normal Version 8 call, without an independent transcript/audio review. See confirmation-fix.md.
- **Historical limits:** Version 8 was live when this entry was written; Version 19 is now live, as recorded in [readiness](readiness.md). No repeat of the superseded Version 7 stress-call script is required. Live speech retesting of the split-number edge case remains unverified. The current-contract S5 checkpoint reflects logging before the spoken handoff; the assignment's handoff is a spoken mock, not a real transfer. Prior tests and failures remain in the voice-tuning evidence. The Version 6 closing mechanism is released; the conditional amount-confirmation follow-up is now live.

## Submission decisions consolidated on 2026-11-05

These extend the November baseline. The four-part architecture and pricing-v1 opening/cap calculation remain; D-43 changes concessions, and D-44 adds the third Twin table for shared negotiation memory. [Readiness](readiness.md) pins deployments, measurements and remaining pilot gates.

### D-36: Consent belongs to a shipment, not just a load ID

- **Why:** fresh TMS reads could change lane, ZIP, equipment or appointment while an earlier price acceptance still reserved the load. A durable hold could also outlive a failed agreement write.
- **Choice:** store the quoted material terms, compare them at acceptance and rep preflight, and require a matching finalized source-call agreement before submission. Stable freight keeps the safe standing quote and lowest ask. A changed shipment requires a fresh pitch while retaining the global round budget. Unsafe or contradictory upstream text goes to review before speech.
- **Tradeoff:** conservative validation can withhold otherwise usable freight, and interrupted holds need rep follow-up or release. It avoids treating an internal intent or changed shipment as carrier consent. See [consent boundary](../ARCHITECTURE.md#10-reservation-and-confirm) and the retained review reproductions.

### D-37: An authenticated viewer is not automatically a rep or a carrier

- **Why:** a valid App login alone grants no booking authority; the real platform returns an `id` field rather than the earlier fixture's `sub`. Shared demo-inbox access does not identify a carrier, and per-call mail limits can be bypassed with new sessions.
- **Choice:** validate the platform identity response into one subject, require an exact rep assignment, enforce canonical-origin writes, and require an enrolled contact roster plus per-reservation trusted delivery evidence for real sends. Caller-supplied identities and contact destinations cannot authorize. SMTP admission adds four attempts per recipient and 100 total per ten minutes across call IDs.
- **Tradeoff:** operators and contacts need explicit onboarding. Email throttling is in-memory per process and resets on restart, so shared provider admission is required before scale-out. The demo inbox remains usable only with booking sends off. [Configuration and rollback](proposal.md#pilot-configuration-and-rollback).

### D-38: Share fresh point reads, never cache mutable decision state

- **Why:** repeated row reads exhausted Twin's four-statements-per-second budget during full call bursts, despite passing ordinary tests. Raising the voice deadline or bypassing pacing would hide the bottleneck.
- **Choice:** batch keys waiting for the same paced SQL slot, detach before dispatch, isolate each waiter's result and cancellation, and force later reads and CAS conflicts through a fresh query. Bound admission to 256 waiters and each query to 128 keys. Writes remain independent version checks.
- **Tradeoff:** a small asynchronous coordinator adds cancellation and freshness obligations. Its explicit race tests and [paired full-flow profiles](readiness.md#concurrency-and-read-budget) justify the complexity; no production call-rate guarantee follows.

### D-39: Show a complete bounded snapshot or an unavailable state

- **Why:** the actual Twin API truncates at 500 rows or one million bytes. A successful HTTP response can therefore omit history and corrupt KPI denominators. Growing-history scans also exceeded the former ten-second App budget.
- **Choice:** ordered 100-row keyset pages, a twenty-page completion bound per table and strict truncation/ordering checks. Cache for five seconds after completion; allow twenty seconds for operations fetches and suppress overlapping refreshes. The voice deadline stays twelve seconds.
- **Tradeoff:** exactly twenty full pages and oversized pages fail closed. Separate table reads are not a transactional snapshot. Retention and real shared-quota sizing remain pilot work; partial success is never reported as complete history.

### D-40: Unify reviewable records while preserving origin and write eligibility

- **Why:** switching between trial and desk views concealed useful history, while a fixed 49-run whitelist hid new calls. Reusing copied historical rows or guessing recording links would misrepresent evidence.
- **Choice:** Overview deduplicates UUID-shaped call IDs from the complete snapshot, across deployment tags. Historical native inventory enriches known durations and endings instead of restricting admission. Active calls contribute to progress; losses require end evidence. Reservation history stays per call, latest state per load. Imports are immutable even when released. Fresh media links require configured workflow provenance stamped at creation; known historical runs are the fallback.
- **Tradeoff:** UUID admission is not platform attestation, and the integration key must remain exclusive to its workflow. Mixed development history is useful operational evidence, not a customer conversion estimate. Source tags still enforce sends; D-21's real-only policy remains only in legacy service diagnostic fields. [Exact formulas](kpis.md).

### D-41: Gate voice behavior with both checkpoint and actual audio evidence

- **Why:** passing text checkpoints did not catch premature search on partial speech, missing audible endings or amount-confirmation failures. Final-offer refusal also needs explicit tool intent to distinguish it from a retry.
- **Choice:** Version 15 asks for missing details one at a time, waits for the lane, reads back corrected totals before mutation, binds final refusal explicitly, and speaks the truthful close before ending. Keep exact prompt/tool hashes, failed native grades and actual overlapping diagnostic audio as separate evidence layers.
- **Tradeoff:** clarification costs turns, generated diagnostic callers do not prove human naturalness, and text grades cannot substitute for speech. Historical Version 15 evidence is 71/74 native checkpoints and three overlapping actual audio scenarios. Version 19 has two raw sweeps (70/74 and 73/74), ten focused passes and a complete diagnostic audio journey; a new owner human call remains required. [Versioned results](readiness.md#native-conversation-evidence).

### D-42: Reproduce locally without credentials; deploy only to an explicit target

- **Why:** a service-only Docker command did not demonstrate a usable App, while an implicit cloud target could overwrite the preserved release. Local auth fixtures also hid the native identity-contract defect.
- **Choice:** `make review` starts the complete disposable App/service/identity/TCP fixture, with the observed native identity shape and real browser-confirm acceptance. `make deploy APP=... APP_URL=...` requires preconfigured resources, checks authenticated service and TMS readiness, and opens the named App. Native App/workflow publication remains a separate action.
- **Tradeoff:** the local fixture proves the application path, not external carrier identity or TMS behavior. Cloud one-time setup and secrets are explicit prerequisites, not falsely claimed automation. [Commands and accepted checks](readiness.md#reproduce-the-application).

## Earlier decisions

| ID | Decision | Status |
|---|---|---|
| D-1 | One Python/FastAPI service | Active |
| D-2 | Twin is the only datastore | Active |
| D-3 | The service sends codes through an email provider | Active. Gmail SMTP proven live. |
| D-4 | Versioned pricing with a keyed gap below the ceiling | Active |
| D-5 | No cached loads; report a TMS outage honestly | Active |
| D-6 | Separate `ACK_PENDING`, `CONFIRMED`, `UNKNOWN`; never resend | Active |
| D-7 | One service instance | Active. Coordination is by version check alone, without process-local reservation locks; pacing and refresh have local locks. |
| D-8 | Send `LOAD_BOOK` at rate agreement | **Replaced by D-22** |
| D-9 | OTP on every call | Active |
| D-10 | `MAX_BUY` supplies `max_rate`, subject to validation | Active |
| D-11 | No usable ceiling means pricing review | Active |
| D-12 | Codes go to one configured demo inbox | Demo exception only; trusted roster required for sends under D-37 |
| D-13 | Record turned-away demand | Active. Derived from call rows, with no table. |
| D-14 | Carrier view in the operations app | Deferred to optional additions |
| D-15 | Northstar is a handoff per verified call | Clarified: recorded reservations per call that ever passed its code; not proof of a spoken handoff |
| D-16 | `run_id` is the only call identity, in a hidden field | Active |
| D-17 | Retries recognized by request fingerprint | **Replaced by D-26** |
| D-18 | Neutral wording on `UNKNOWN`; no Confirm on `UNKNOWN` | Retired. The agent takes no part in the send, so it never has to describe `UNKNOWN`, and Confirm applies only to `RESERVED`. |
| D-19 | `service/` on `main` is the submission source | Active. Main was fast-forwarded to the reviewed release; `oldmain` and local tag `baseline-v8` retain `15ce2b6`. Deployment state is recorded in readiness, not inferred from Git. |
| D-20 | No standalone test bookings | Active. The owner authorized one exception on 2026-11-02: two probe sends, recorded in [tms-contract.md](tms-contract.md). |
| D-21 | Real and synthetic calls kept apart | Tags and send guards remain; unified App reporting supersedes a separate-view requirement under D-40 |

Each original decision's full reasoning is in [architecture v2.5](https://github.com/sgon0181/happyrobot-inbound-carrier-sales/blob/prototype/e2e/ARCHITECTURE.md#12-decisions-and-open-questions).

## Reporting and the rep workspace

The November 4 baseline report used a fixed, reconciled 49-call native inventory. That sample remains dated evidence in [KPI definitions](kpis.md). The current App admits new UUID-shaped call rows automatically, with historical inventory used only to enrich evidence, and shows all recorded agreements by default (D-40). The load ID alone remains insufficient for historical review because a released load may later belong to another call; links carry both load and run IDs.

## Open checks

| ID | Question | State | If it fails |
|---|---|---|---|
| T-1 | Do Twin version checks and primary keys hold? | Proven on probes and real tables, and on the new `calls` table from Fly on 2026-11-03: insert, version-checked update, and a stale update refused. `id` is the primary key of all three current tables; later negotiation-table provisioning and readback are recorded in readiness. | Small Postgres for coordination, justified under PDF p.4 |
| T-2 | What do `PENDING`, currency and bounds mean? | Q8 answered on November 5 for the demonstrated handling. External finalization is unspecified. Currency and rate bounds remain open under Q3. [Clarifications](questions.md) | Show the actual status and disclose the assumption |
| T-3 | Can the service deliver codes? | Proven: Gmail SMTP from Fly | |
| T-4 | Does `run_id` arrive outside model arguments? | Proven on the prototype, and on the real workflow on 2026-11-03: the model's tool arguments held only the MC and code, and the Twin row is keyed by the run's ID. | |
| T-5 | Can the service reach FMCSA? | Proven from Fly `iad`, again by the new service on 2026-11-03. The local machine gets HTTP 403. | Native HTTP node passes the raw result |
| T-6 | Can the agent end a voice session and speak the handoff? | Historical failures and V6/V8 limits remain in their release evidence. Exact V15 actual audio completed three overlapping diagnostic-caller scenarios, with a truthful agreement recap or refusal, single goodbye and agent hangup. A new owner human call remains separate. [Evidence](readiness.md#native-conversation-evidence) | |
| T-7 | Why does the Apps gateway to Twin fail? | Open, and designed around by D-30 | |
| T-8 | Can a native post-call node produce a summary for the close request? | Optional and untested. No longer a dependency: R3 stores structured decisions and best-effort model closing notes, with end reporting separate. | Show absent notes honestly; do not invent a post-call summary |
| T-9 | Should workflow run dumps store full transcripts in Twin natively? | Not tested. They would add spoken codes to Twin. | Transcripts stay on the platform |
| T-10 | Does the platform retry tool calls? | Unknown. D-26 is safe either way. | |


## Decisions made on 2026-11-07

### D-43: Reciprocal negotiation with a meaningful concession floor

- **Why:** fixed round targets rewarded inflated anchors. The first reciprocal rule stopped that ladder but rounded a 2% allowance to zero for openings below $1,250; half of a $25 carrier improvement also rounded to zero. Valid deals stalled with a $25 gap despite available room.
- **Choice:** `reciprocal-v2` moves toward a carrier who moves toward us. An ask must be within 25% above the opening. After the first ask, it must improve the best prior ask by at least $25. Move one third of the gap to the lower of ask and private cap, rounded down to $25, with a $25 minimum; stop at the cap if less room remains. Accept the caller's exact amount when it is at or below our standing or next offer. Keep pricing-v1 and its HMAC draws unchanged.
- **Controls:** distant, rising and token asks hold. A new above-offer ask spends a round even when held; exact replays do not. Three rounds, final refusal and lower-cap retraction remain unchanged. Each new call negotiation event and shared decision event carries `negotiation_policy_version`; historical events keep their original fields and values.
- **Tradeoff:** the floor and wider reach improve small-gap conversion but allow larger concessions than the original 2% rule. A descending ask inside the reachable band can earn money, even if it began at a distant anchor. These are explicit brokerage policy choices, not market estimates, optimal-strategy claims or immunity from probing. The cap and durable budget bound exposure. [Before/after examples and adversarial results](negotiation-review.md) show the cost.
- **Release:** service source `8ccbf0a` was deployed with owner approval on November 7. Runtime hashes, authenticated health, TMS reachability and guarded settings passed. Existing Version 19 speech evidence belongs to the prior rule; the new diagnostic voice check remains pending. No prompt or workflow change accompanies this patch.

### D-44: A third Twin table holds durable carrier/load memory

- **Why:** per-call limits alone let a caller redial, restart or switch voice versions to obtain another concession budget. The shared budget belongs to the verified MC and material shipment, not the session.
- **Choice:** `negotiations` uses the same `id`, `version`, `data` shape as calls and bookings, keyed by normalized MC and load ID. It stores the standing offer, best ask, spent rounds, seen asks, shipment facts and decision events. It is already provisioned in Twin staging. Every new call still verifies and searches independently.
- **No expiry:** waiting does not reset the budget. Price-only changes do not reset it either; lower limits durably retract the quote. A material shipment change begins a fresh shared negotiation while preserving the call-wide three-round limit. Explicit operator repricing and retention are future operations, not caller capabilities.
- **Write boundary:** shared CAS precedes call CAS. A failed call write may leave a concession spent without it being heard; this prevents retries from refunding money. The unchanged opening-acceptance optimization skips a redundant write only after a fresh absent-row read with no spent rounds. There is no cross-table transaction. [Capacity evidence](reciprocal-capacity.md) records the measured cost and repair.
- **Tradeoff:** this adds reads and writes and requires retention planning; it intentionally favors a durable budget over time-based flexibility. No old rows are reset, backfilled or reinterpreted. New events are versioned under D-43. Memory follows an MC, not a uniquely authenticated human dispatcher; demo inbox access does not establish real carrier identity.
