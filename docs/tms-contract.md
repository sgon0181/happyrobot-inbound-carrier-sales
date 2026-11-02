# TMS Contract Evidence

What we have observed about the legacy TMS, what those observations do not prove, and which loads are set aside for testing. Start with the [shared TMS operating reference](tms/README.md) for command usage. This evidence adds to the [TMS handbook](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/) and does not replace it.

There are two kinds of evidence here, and they are not interchangeable:

| | [2026-10-30 study](#study-2026-10-30) | [One lookup](#one-lookup) |
|---|---|---|
| **Covers** | 302 full load records, plus search and error behaviour | One load, at the moment it runs |
| **Re-run from this repo?** | No. Raw replies and study code are kept locally in the Git-ignored `secrets/tms-assessment-20261030/` | With the read-only reader, on branch `prototype/e2e` until slice 1 |
| **Use it for** | Design decisions | Confirming that the field and our token still work |

## Study: 2026-10-30

A read-only snapshot (Australia/Sydney) using one token. It made 537 request attempts across 461 cases: 417 `LOAD_GET` and 120 `LOAD_QUERY`. No `LOAD_BOOK` was sent.

It retrieved 302 unique full records: 50 open and 252 expired. Searches by all 50 US states and by equipment type found the same 50 open loads. Expired loads came from a bounded ID range plus sampling, so they are not a complete list. Later inventory, or another token, may differ.

| Area | Observed | Build implication |
|---|---|---|
| **Pricing** | All 302 full records have whole-number `RATE` and `MAX_BUY`. `MAX_BUY` is always above `RATE`, by 5.0% to 24.9% of `RATE` (median 14.8%; 12.1% on open loads). The handbook samples show the reverse. | Compare the two values on each load. Keep the missing-ceiling path. |
| **Search vs detail** | No `LOAD_QUERY` summary contained `MAX_BUY`. | Call `LOAD_GET` before pricing. |
| **Stability** | 40 repeated reads of LD01023 returned one identical record, once faults were retried. | Stable during the test, which does not prove prices never change. Re-read before booking. |
| **Search inputs** | Accepted equipment: `DRY_VAN`, `REEFER`, `FLATBED`, `STEP_DECK`, `POWER_ONLY`. Others return `MISSING_FIELD`. Equipment and state must be uppercase; city matching ignores case and accepts partial names. `PICKUP_DATE` takes `YYYYMMDD`. | Normalize inputs, then check that returned loads match. |
| **Ignored inputs** | Unknown fields are silently ignored, including plausible names such as `PICKUP_FROM`. | A successful reply does not prove a filter was applied. |
| **Result limits** | Tested `MAX_RESULTS` values from 1 to 1000 were accepted; zero, negative and non-numeric values were rejected. The largest reply held 32 records. The server's own cap is unknown. | Do not rely on a fixed maximum. Search order was not established, so sort deliberately. |
| **Error codes** | An unknown load returned `NOT_FOUND`; the handbook shows `UNKNOWN_LOAD`. | Handle both, and keep a fallback for unlisted codes. |
| **Reply size** | Whole replies reached 7,941 bytes. The longest line was 526 bytes. | The handbook's 4096-byte frame limit cannot mean the whole reply. Check it per line, bound the whole reply separately, and stop reading at the `END` line. |
| **Faults** | 76 of 537 attempts (14.15%) had detectable timeouts, partial replies or malformed replies. With up to 3 attempts, all 461 cases ended in a valid reply. Replaying all 537 stored replies through the exact `END` rule changed none of these results. | A reply is complete only if it is one CRLF-terminated `ERR` line or finishes with a whole CRLF-terminated line equal to `END`. A suffix check is not enough: `NOTES:WEEKEND\r\n` must fail. Bounded read retries are required. Never auto-retry a write. |
| **Latency** | Good attempts took about 0.96 s (median) and 1.04 s (95th percentile) from a local machine. 33 cases used more than 6 s of attempt time, with a 5 s receive timeout. | The ~6 s read budget needs shorter per-attempt timeouts. Fly.io latency is untested. |
| **Load data** | 212 records have blank notes. 10 contradict themselves on driver assist and no-touch, including LD01023. 10 mention $75/h detention. All `DIMS` values use feet, while the PDF specifies inches. No schedule was invalid or backwards. | Show contradictory notes as written and flag them for the rep. Convert dimensions deliberately. |

## One lookup

From a checkout of `prototype/e2e`:

```bash
python3 scripts/query_loads.py --load-id LD01023
```

Last run 2026-10-31 00:58 UTC: `RATE` 2709, `MAX_BUY` 2922, `STATUS` OPEN and 19 fields, matching the study's record for that load.

This reproduces one load's current values, and shows that `LOAD_GET` still returns `MAX_BUY` to our token. It does not reproduce the study's counts, ranges or fault rates, and says nothing about other loads, other tokens or booking.

LD01023's pickup is dated 2026-10-31, so its `STATUS` may change. That would not contradict the study. The 252 expired records still carried both prices, but that is not guaranteed for this load.

Without `--load-id`, the script runs a `LOAD_QUERY` for up to 3 dry-van summaries, or the number set with `--limit`. Summaries do not include `MAX_BUY`.

## Field mapping

| TMS field | PDF field | Basis |
|---|---|---|
| `RATE` | `loadboard_rate` | Handbook: posted rate |
| `MAX_BUY` | `max_rate` | Candidate only (D-10): present on every record read, not confirmed by Luke |

The remaining fields are mapped when the TMS adapter is built.

## Booking experiments: 2026-10-31

The initial controlled study sent five `LOAD_BOOK` requests across four disposable loads: four complete reference-bearing `PENDING` acknowledgements and one explicit `INVALID_RATE` rejection. A separate, deliberately authorized exact replay added one `ALREADY_BOOKED` response. Combined: **six write sends, four load IDs, zero observed `BOOKED` responses**. Count sends, not the journal's multiple intent/result/classification entries. This was one token and one handbook-example MC, which FMCSA showed as inactive on 2026-10-31, without an FMCSA/OTP call flow; it is not an end-to-end verification test.

| Historical case | Load | `AGREED_RATE` text | Observed immediate result |
|---|---|---|---|
| Equality with freshly read ceiling | LD01086 | `7900` | Reference and `PENDING` |
| Whole value written with `.00` | LD01082 | `2142.00` | Reference and `PENDING` |
| Actual fractional value | LD01081 | `1324.50` | `INVALID_RATE`: positive integer required |
| Low positive whole value | LD01075 | `1` | Reference and `PENDING` |
| Integer control after explicit rejection and fresh `OPEN` read | LD01081 | `1324` | Reference and `PENDING` |
| Later exact replay of acknowledged pending request | LD01086 | `7900` | `ALREADY_BOOKED`; remained `PENDING` |

These are past test inputs, not prices to offer or commands to replay. No above-ceiling request was sent. Canonical integer serialization of an exact positive whole native value is supported by this sample; `.00` acceptance disproves a strict digits-only input requirement. Reject unsupported fractions without rounding an agreement. Currency, scale, complete syntax, full bounds, later validation and server enforcement of `MAX_BUY` remain unproven. A positive value of `1` passing initial validation is not a confirmed one-dollar booking or a useful pricing policy.

All four loads remained `PENDING` roughly 40 minutes later. The separate replay experiment left the target and untouched control pending, including a check about 74.5 seconds after its error. These windows establish what had happened by those times, not a permanent state or processing SLA.

| Additional observation | Implementation consequence |
|---|---|
| `LOAD_QUERY` still returned all four `PENDING` loads. | Search is not an `OPEN`-only guarantee. Offer only explicitly `OPEN`, future-eligible loads after local exclusions. |
| Full readbacks retained 19 fields, without booking reference, MC, agreed rate, currency or pending reason/expiry. | Persist the direct acknowledgement immediately. A status-only read cannot reconstruct or prove carrier/rate ownership. |
| Exact replay returned `Already booked by this token` without finalizing. | It demonstrates token-associated state, not confirmation or a safe general retry rule. |
| Nine supplied handbook pages, portal controls and the assignment supplied no confirmation operation. | No supported finalization action was established. Do not guess confirmation fields/commands or treat local approval as external finalization. |

An early harness classified the first pending receipt as unknown before `PENDING` support was added. Correcting that local classification was neither another send nor a server transition. Preserve three distinct outcomes: `ACK_PENDING` for a valid pending receipt, `UNKNOWN` for ambiguous transport/framing, and `CONFIRMED` for authoritative final evidence. Pending and unknown do not count in confirmed-booking KPIs.

### Active-MC attempt on a real call

On 2026-10-31 a real browser call through Codex's lab sent one `LOAD_BOOK` for LD01077 with MC 138328, which FMCSA showed as active, at rate 3225 with no counter rounds. Fresh `OPEN`, pickup and ceiling checks passed just before the send. The attempt ended `UNKNOWN` with no receipt or reference. A lab defect discarded the error type and raw reply, so the failing step is unknown: the 0.306 seconds it took does not show whether the network or the save failed.

Later reads returned `PENDING` at roughly 54, 320 and 1,408 seconds, never with a reference. One read-only reconcile kept the booking `UNKNOWN`. Nothing was resent. The planned control, LD01069 with MC 872144, was not sent, because the first unknown outcome stops the campaign. Replaying the six earlier replies through the lab's parser found no framing failures, so that does not explain this result.

At that point: **seven write sends, five load IDs, zero observed `BOOKED` responses**. This does not establish a cause. The read makes a carrier-specific cause less likely, but the reply is gone and reads show no ownership. No further standalone booking test is planned ([D-20](decisions.md)).

### Sanitized evidence and reproduction limits

[`tms/fixtures/booking-replies.json`](tms/fixtures/booking-replies.json) freezes the six replies with original booking references replaced by synthetic identifiers. Its [README](tms/fixtures/README.md) explains transformations and offline use. It includes no credentials and is available in a fresh clone. These fixtures preserve observed framing; they do not reproduce the real experiment or prove final confirmation.

Original study sources remain Git-ignored: `secrets/tms-booking-test-20261031/summary.json`, `requests.jsonl` and `inventory.json`; the analogous summary/request files in `secrets/tms-confirmation-probe-20261031/` and `secrets/tms-pending-investigation-20261031/`. The lab's `secrets/tms-architecture-lab-20261031/EVIDENCE_INDEX.txt` indexes them. Local copies may be unavailable in another checkout. Do not run historical booking harnesses to review saved evidence; some stages perform real writes.

### Offline booking-policy lab

The separate ignored architecture lab records **37 passing behavioral tests**, five simulated lifecycle traces and the six captured replies above. It exercises pending/confirmed/unknown separation, durable write intent, duplicate actions, concurrent approvals, restart ambiguity, blocked expiry and late-result guards. These are historical recorded results, not new tests run by this documentation change or a shipped production test suite.

The lab uses SQLite and fake TMS services. Its back-office finalization and enriched ownership fields are simulator fixtures, not real server capabilities. It does not validate Twin transactions/latency, FMCSA, OTP delivery, trusted call identity, the deployed voice workflow, Apps or pricing confidentiality. Booking timing is now [D-22](decisions.md): send at the rep's Confirm. The lab is reference material, not coverage of that path. No further live booking probe is required to start the read adapter and policy/storage interfaces.

### Prototype sends, 2026-11-01

The prototype sent three more `LOAD_BOOK` requests on real owner calls, all with active MC 138328. Full detail, receipts and hashes are in `docs/tms-contract.md` and `docs/prototype-evidence/` on branch `prototype/e2e`.

| Load | Rate | Result | Note |
|---|---|---|---|
| LD01094 | 1075 | Complete `PENDING` receipt | Sent before the caller clearly agreed. Flagged for consent review, and never to be confirmed. |
| LD01085 | 2950 | Complete `PENDING` receipt | Clear permission. Shortened spoken handoff. |
| LD01062 | 3625 | Complete `PENDING` receipt | The clean run, `5783608f-d54b-4a5d-b028-89db98ae10ec`. |

- An active MC also returned `PENDING`, so inactive authority cannot explain every acknowledgement. It does not establish what causes finalization, or prove that `PENDING` is a reservation.
- A rep's approval in the app left the TMS status at `PENDING`.
- The container's receipt journal was lost after an automatic stop and start. The reply survived in Twin and the local export.

All together: **ten write sends across eight load IDs: seven complete `PENDING` acknowledgements, two explicit errors, one `UNKNOWN` and zero observed `BOOKED`.**

## Booking test inventory

All statuses below are historical snapshots, not current availability. These IDs are sandbox test inventory, not credentials. The service reads the same list from [`blocked-loads-v1.json`](../service/policy/blocked-loads-v1.json).

| Purpose | IDs | Required handling |
|---|---|---|
| Spent, acknowledged `PENDING` | LD01086, LD01082, LD01081, LD01075, LD01094, LD01085, LD01062 | Keep blocked from offers and further booking sends until authoritatively resolved. |
| Spent, outcome unknown | LD01077 | Keep blocked from offers and further booking sends. Never resend: no receipt or reference exists. |
| Voided control | LD01069 | Never offer or book. |
| Protected, historical `OPEN` snapshot | LD01023, LD01032, LD01036 | Do not spend on write probes. Re-read status, schedule and ceiling before any demo; protection does not guarantee continued availability. |

The board refills: between the 2026-10-30 study and the 2026-10-31 tests, 8 load IDs left, 8 new ones appeared, and search still returned 50 records. That is one day's observation, not a guarantee. No reset/cancellation mechanism or pending lock across tokens was established. The original acknowledgement references stay in the private journal; synthetic fixture references cannot be used for live reconciliation. Before any newly authorized booking experiment, record its inventory and one-shot intent separately from demo loads.

## Still unproven

- **Booking contract (T-2):** currency/scale, full format and bounds, server ceiling enforcement, finalization/rejection/expiry, cancellation/reset and authoritative ownership recovery after a lost acknowledgement. The handbook's own sample books `AGREED_RATE:2200` on a load with `MAX_BUY` 1950, which hints the server may not enforce the ceiling. A sample is not proof.
- **Cause of `PENDING`:** the first acknowledgements used MC 872144, which FMCSA shows as inactive, but later ones used active MC 138328, so inactive authority cannot explain them all. Every send used one candidate token, so a token-specific cause is still open.
- **Other integrations:** [platform checks](platform-checks.md) record what Codex's experiment settled and left open. None of it is established by the older SQLite lab.
- **Extra charges:** how detention and similar terms relate to `RATE` and the ceiling.
- **Pickup times:** which timezone `PICKUP_DT` uses.
- **Pricing bands:** running `pricing-v1` offline over the 50 saved open loads with 200 random secrets sent none to pricing review. A median of 2 loads (at most 5) got a working cap at or below `RATE`, and a median of 1 (at most 3) had round targets collapse after $25 rounding. Those dollar-labelled policy values remain demo assumptions until money scale is confirmed.

[questions.md, Q8](questions.md) retains the unanswered owner clarification. The first-layer tentative outcome is a documented interpretation; it does not prove `PENDING` reserves a load or that a local senior approval can finalize the external TMS.
