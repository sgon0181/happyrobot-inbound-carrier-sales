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

## Still unproven

- **Booking rates (T-2):** accepted money units, precision and bounds, and whether the server enforces `MAX_BUY`. Reads cannot settle this. The newer owner-recorded Q8 evidence below does not establish the complete validation contract.
- **Booking ownership and final status (T-2):** no confirmed booked record was retrieved in the read-only study. Q8 records newer `PENDING` acknowledgements; no authoritative transition to `BOOKED` or final-confirmation operation has been established.
- **Extra charges:** how detention and similar terms relate to `RATE` and the ceiling.
- **Pickup times:** which timezone `PICKUP_DT` uses.
- **Pricing bands:** with a 6% gap and $25 rounding, 7 of the 50 open loads would get a working cap at or below `RATE`; with a 2% gap, none would. Check this against the pricing policy before the demo.

## Booking test inventory

The 2026-10-30 study above sent no bookings. Since that study, the owner recorded four disposable live booking tests in [`Questions.Md`, Q8](../Questions.Md): requests within fresh `MAX_BUY` values received booking references and `STATUS:PENDING`, and remained pending roughly 40 minutes later. This is owner-recorded evidence, not a replayable test record in this file. The disposable load IDs, exact requests and replies have not yet been recorded here; do not assume any particular load is still unused.

The handbook shows `BOOKED` and documents no confirmation operation. Q8 asks Luke what final confirmation requires; no answer is recorded. An acknowledgement with `PENDING` must remain pending in the UI and must not count as a confirmed booking. The current first-layer interpretation and its unresolved booking-timing decision are recorded in Q8; `ARCHITECTURE.md` still needs to consolidate this newer evidence.

Before further live booking tests, record the disposable load IDs here, separately from inventory kept for the demo. Do not use a load merely because it appears in a handbook example or an earlier read-only lookup.
