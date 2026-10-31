# TMS Contract Evidence

What we have observed about the legacy TMS, what those observations do not prove, and which loads are set aside for testing. Start with the [shared TMS operating reference](tms/README.md) for command usage. This evidence adds to the [TMS handbook](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/) and does not replace it.

There are two kinds of evidence here, and they are not interchangeable:

| | [2026-10-30 study](#study-2026-10-30) | [One lookup](#one-lookup) |
|---|---|---|
| **Covers** | 302 full load records, plus search and error behaviour | One load, at the moment it runs |
| **Re-run from this repo?** | No. Raw replies and study code are kept locally in the Git-ignored `secrets/tms-assessment-20261030/` | Yes, with the command below |
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
| **Faults** | 76 of 537 attempts (14.15%) had detectable timeouts, partial replies or malformed replies. With up to 3 attempts, all 461 cases ended in a valid reply. Replaying all 537 stored replies through the exact `END` rule changed none of these results. | A reply is complete only if it is one CRLF-terminated `ERR` line or finishes with a whole CRLF-terminated line equal to `END`. A suffix check is not enough: `NOTES:WEEKEND\r\n` must fail. `python3 scripts/test_query_loads.py` covers this offline. Bounded read retries are required. Never auto-retry a write. |
| **Latency** | Good attempts took about 0.96 s (median) and 1.04 s (95th percentile) from a local machine. 33 cases used more than 6 s of attempt time, with a 5 s receive timeout. | The ~6 s read budget needs shorter per-attempt timeouts. Fly.io latency is untested. |
| **Load data** | 212 records have blank notes. 10 contradict themselves on driver assist and no-touch, including LD01023. 10 mention $75/h detention. All `DIMS` values use feet, while the PDF specifies inches. No schedule was invalid or backwards. | Show contradictory notes as written and flag them for the rep. Convert dimensions deliberately. |

## One lookup

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

The initial controlled study sent five `LOAD_BOOK` requests across four disposable loads: four complete reference-bearing `PENDING` acknowledgements and one explicit `INVALID_RATE` rejection. A separate, deliberately authorized exact replay added one `ALREADY_BOOKED` response. Combined: **six write sends, four load IDs, zero observed `BOOKED` responses**. Count sends, not the journal's multiple intent/result/classification entries. This was one token and one handbook-example MC, without an FMCSA/OTP call flow; it is not an end-to-end verification test.

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

### Sanitized evidence and reproduction limits

[`tms/fixtures/booking-replies.json`](tms/fixtures/booking-replies.json) freezes the six replies with original booking references replaced by synthetic identifiers. Its [README](tms/fixtures/README.md) explains transformations and offline use. It includes no credentials and is available in a fresh clone. These fixtures preserve observed framing; they do not reproduce the real experiment or prove final confirmation.

Original study sources remain Git-ignored: `secrets/tms-booking-test-20261031/summary.json`, `requests.jsonl` and `inventory.json`; the analogous summary/request files in `secrets/tms-confirmation-probe-20261031/` and `secrets/tms-pending-investigation-20261031/`. The lab's `secrets/tms-architecture-lab-20261031/EVIDENCE_INDEX.txt` indexes them. Local copies may be unavailable in another checkout. Do not run historical booking harnesses to review saved evidence; some stages perform real writes.

### Offline booking-policy lab

The separate ignored architecture lab records **37 passing behavioral tests**, five simulated lifecycle traces and the six captured replies above. It exercises pending/confirmed/unknown separation, durable write intent, duplicate actions, concurrent approvals, restart ambiguity, blocked expiry and late-result guards. These are historical recorded results, not new tests run by this documentation change or a shipped production test suite.

The lab uses SQLite and fake TMS services. Its back-office finalization and enriched ownership fields are simulator fixtures, not real server capabilities. It does not validate Twin transactions/latency, FMCSA, OTP delivery, trusted call identity, the deployed voice workflow, Apps or pricing confidentiality. The old mandatory timing recommendation is superseded: timing remains explicit candidate policy in architecture D-8. No further live booking probe is required to start the read adapter and policy/storage interfaces.

## Booking test inventory

All statuses below are historical 2026-10-31 snapshots, not current availability. These IDs are sandbox test inventory, not credentials.

| Purpose | IDs | Required handling |
|---|---|---|
| Disposable, acknowledged `PENDING` | LD01086, LD01082, LD01081, LD01075 | Keep blocked from offers, expiry/release cleanup and further booking sends until authoritatively resolved. |
| Protected for demo, last observed `OPEN` | LD01023, LD01032, LD01036 | Do not spend on write probes. Re-read status, schedule and ceiling before any demo; protection does not guarantee continued availability. |

No reset/cancellation mechanism or pending lock across tokens was established. The original acknowledgement references stay in the private journal; synthetic fixture references cannot be used for live reconciliation. Before any newly authorized booking experiment, record its inventory and one-shot intent separately from demo loads.

## Still unproven

- **Booking contract (T-2):** currency/scale, full format and bounds, server ceiling enforcement, finalization/rejection/expiry, cancellation/reset and authoritative ownership recovery after a lost acknowledgement.
- **Other integrations:** Twin atomicity/latency (T-1), notification-log exposure (T-3), trusted call/operation identity (T-4), FMCSA fixtures and OTP delivery. None is established by the SQLite lab.
- **Extra charges:** how detention and similar terms relate to `RATE` and the ceiling.
- **Pickup times:** which timezone `PICKUP_DT` uses.
- **Pricing bands:** with a 6% gap and $25 rounding, 7 of the 50 open loads would get a working cap at or below `RATE`; with a 2% gap, none would. Those dollar-labelled policy values remain demo assumptions until money scale is confirmed.

[Questions.Md, Q8](../Questions.Md) retains the unanswered owner clarification. The first-layer tentative outcome is a documented interpretation; it does not prove `PENDING` reserves a load or that a local senior approval can finalize the external TMS.
