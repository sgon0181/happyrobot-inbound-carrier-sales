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

## What ports unchanged

Both audits judged these sound. They come across in slice 1 with their tests.

| File on `prototype/e2e` | Lines |
|---|---:|
| `service/adapters/tms/protocol.py` | 120 |
| `service/adapters/tms/mapping.py` | 78 |
| `service/core/money.py` | 20 |
| `service/core/negotiation.py` | 41 |
| `service/core/pricing.py` | 88 |
| `service/core/loads.py` | 28 |
| `service/core/models.py` | 48 |

`pricing.py` loses its file loader, which moves to `config.py` with validation. `negotiation.py` gains precondition checks. Tests worth porting are `test_protocol.py`, `test_pricing.py`, the fault-injection cases in `test_client.py`, and `adapters/tms/fake.py` as a test fixture.

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
