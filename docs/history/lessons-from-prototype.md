# Lessons from the prototype

Codex built a full end-to-end system from architecture v2.5 and it worked. It lives on branch `prototype/e2e` at `4b5ef3a`, with its complete report in `PROTOTYPE_REPORT.md` there. This page keeps what the real build needs. The full analysis is in the two [audits](audits/).

## What it proved live

On owner run `5783608f-d54b-4a5d-b028-89db98ae10ec`, one call passed every step: active MC, emailed code, a real counter (4200 countered at 3600, agreed at 3625), a TMS reference with `PENDING`, the spoken mocked transfer, the agent hanging up, a complete Twin record and a rep action in Apps.

| Proven | Still needs proving on the new build |
|---|---|
| FMCSA lookup from Fly | Reservation by primary key on the new `bookings` table |
| Gmail SMTP code delivery, read back on a call | `LOAD_BOOK` triggered by Confirm |
| Version-checked writes and primary keys on real Twin tables | A native post-call summary (T-8) |
| `run_id` reaching the service outside model arguments | Capacity at the estimated 20 statements per call |
| The built-in hang-up tool ending a voice call | |
| Apps reading through the service with a verified rep identity | |

## What it taught

| Lesson | Consequence in v3 |
|---|---|
| An irreversible send inside a voice request creates most of the failure modes | D-22 moves it to the rep's Confirm |
| State spread across rows can stop halfway, as three separate failures showed | D-23: everything that changes together is one row |
| A fire-and-forget audit write can vanish with nothing noticing | Events commit with the state (INV-9) |
| Nothing exposed failures: one log statement, 13 silent error handlers | Handlers log, and failures reach the dashboard |
| A test double that behaves differently from production hides real bugs | Tests run the real SQL against a fake Twin, and every route over HTTP |
| 7 of 235 functions had type annotations, so a green default `mypy` proved nothing | `mypy --strict` from the first commit |
| Field lists written as a denylist leak by default | Load fields reach the agent through an allowlist (INV-2) |
| A two-step consent question made the carrier repeat themselves | The prompt has one acceptance step; the rep reviews |
| Container files do not survive a stop and start | Nothing depends on the local disk |
| A state's name proves nothing: the refused connection became `FAILED`, yet the load stayed blocked | Tests assert the load is actually free |

## What slice 1 kept, and how

Both audits judged these files sound, but none passed the gates in [architecture section 14](../reference/architecture.md#14-quality) as written: no function had type hints, and the files showed 115 lint issues and 95 strict type errors. So slice 1 rewrote each one with the prototype's tests and recorded TMS replies as the check, then compared old and new on the same inputs (D-29).

| Prototype file, lines | Now, lines | Checked by |
|---|---:|---|
| `core/money.py`, 20 | 26 | Identical on 200,000 random inputs |
| `core/models.py`, 48 | 39 | Used by every other test |
| `core/pricing.py`, 88 | 121 | Identical on 300,000 random loads |
| `core/negotiation.py`, 41, and `core/loads.py`, 28 | 58 and 48 | Identical on 159,632 counter-offers and 5,000 searches |
| `adapters/tms/protocol.py`, 120 | 134 | Identical on 500,000 fuzzed replies and requests |
| `adapters/tms/mapping.py`, 78 | 76 | Identical on 120,000 random records, before the timestamp fix |
| `adapters/tms/client.py`, 289 | 151 | The prototype's read tests, ported |

Deliberate differences: negotiation refuses impossible states, the pricing policy must have three whole-number targets to load, timestamps must be exactly 14 digits (a prototype bug that Codex's review found), the reply parser needs no complexity exception, and the booking path waits for slice 4.

## Where the prototype's files went

| On `prototype/e2e` | On `main` | Why |
|---|---|---|
| `core/calls.py`, `core/booking.py` | `calls.py`, `bookings.py` at the top of `service/` | They call Twin, the TMS and email, so they are not pure rules. `core/` has no network or clock. |
| `api/app.py` | `api.py` | A folder holding one file adds nothing |
| `adapters/twin/`, three files | `adapters/twin.py` | Two tables instead of nine (D-23) |
| `adapters/fmcsa/`, `adapters/notify/` | `adapters/fmcsa.py`, `adapters/email.py` | One file each |
| `adapters/tms/fake.py` | `tests/fake_tms.py` | Test doubles live with the tests |
| `adapters/transcripts.py`, `adapters/confirmation.py`, `adapters/tms/evidence.py` | Removed | The consent check, redaction and receipt journal were dropped (D-25) |
| `core/ports.py` | Removed | `TmsUnavailable` sits in the TMS client that raises it. The booking outcome and receipt types return with `LOAD_BOOK` in slice 4. The TMS interface is unneeded, because tests run the real client against a real local fake server. |
| `core/inventory.py` | Removed | It read the blocked-load file from inside `core/` at import. `config.py` will load it at startup in slice 2 and pass it to load selection. |
| `scripts/`, nine scripts | Removed | Deployment becomes `make deploy`, and Twin tables are created in the Twin UI |
| None | `core/carrier_policy.py`, slice 2 | The FMCSA eligibility rule becomes a pure, testable rule instead of living in network code |

## Useful reference

Read these on the branch when building the matching slice; do not copy them across whole.

| Need | Where on `prototype/e2e` |
|---|---|
| The voice prompt and workflow | `happyrobot/prototype-prompt.txt`, `happyrobot/prototype-workflow.json` |
| QA scenarios and Northstars | `happyrobot/qa-scenarios-candidate-v17.json`, `happyrobot/northstars-candidate-v17.json` |
| Dashboard source | `ops-app/` |
| The FMCSA rule as code | `service/adapters/fmcsa/client.py`, `assess` |
| Twin SQL that worked live | `service/adapters/twin/repository.py` |
| The evidence behind every claim | `docs/prototype-evidence/`, `docs/qa-results.md` |
| Build description and email drafts | `docs/build-description.md`, `docs/prospect-email-draft.md` |
