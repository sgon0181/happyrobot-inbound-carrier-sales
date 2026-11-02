# Audit report: inbound carrier sales service

| | |
|---|---|
| **Audited** | `prototype/e2e` at `4b5ef3a` (primary), compared with `main` at `2d08ae1` |
| **Date** | 2 November 2026 |
| **How** | Read-only. Both commits were exported from this folder's own `.git` into a temporary directory. All tools ran there or in throwaway containers. No live system was contacted, and `.env` and `secrets/` were not opened. |

**Read this first.** The files checked out in this folder are not the system the brief describes. `main` is a TMS adapter and booking core: no HTTP endpoints, no Twin, no FMCSA, no email, no dashboard (`service/README.md:3` on `main` says so). The system that passed the real call exists only on the local branch `prototype/e2e`, which has no remote. Earlier project notes treat that branch as reference only and `main` as production, but the brief's description matches the branch, so that is what this report audits. Every `file:line` below refers to `4b5ef3a` unless it says otherwise.

## 1. Verdict

1. **Overall: refactor, do not rewrite.** No double send or ceiling leak was found, but three reproduced defects and the items below block an enterprise claim.
2. **Keep:** `service/adapters/tms/`, `service/policy/`, `service/tests/`, `happyrobot/`, and `pricing`, `negotiation`, `money`, `loads`, `models` in `service/core/`.
3. **Refactor:** `service/core/calls.py` and `booking.py`, `service/adapters/twin/`, the other `service/adapters/`, `service/scripts/`, `ops-app/`.
4. **Rewrite, file scope only:** `service/api/app.py` and `service/config.py`.
5. **First action:** the code must reach `main` and a private remote. It currently exists on one disk.

## 2. Measurements

All results are raw output from this audit, on Python 3.12.16 with the pinned `requirements.txt` (resolved: fastapi 0.121.1, starlette 0.49.3, uvicorn 0.38.0, httpx 0.28.1). Tool versions: ruff 0.17.3, mypy 2.4.1, radon 6.0.1, coverage 7.17.0, vulture 2.16, bandit 1.9.4, pip-audit 2.10.1.

### 2.1 Setup

```bash
git archive prototype/e2e | tar -x -C "$SCRATCH/proto"
git archive main | tar -x -C "$SCRATCH/main"
python3.12 -m venv "$SCRATCH/tools/v312"
"$SCRATCH/tools/v312/bin/pip" install -r requirements.txt ruff mypy radon coverage vulture bandit
```

Tests and reproductions ran with a clean environment under an OS-level deny on all non-loopback traffic, on top of the suite's own guard:

```bash
env -i PATH="$PATH" HOME="$SCRATCH/tools" PYTHONDONTWRITEBYTECODE=1 \
  sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))(allow network-outbound (remote ip "localhost:*"))' \
  coverage run --branch --source=service --omit='service/tests/*' -m unittest discover -s service/tests -t .
```

### 2.2 Tests and coverage

`Ran 187 tests in 7.131s, OK`. Branch coverage from `coverage report --sort=cover`:

| Module | Stmts | Miss | Branch | BrPart | Cover |
|---|---:|---:|---:|---:|---:|
| `scripts/cli_platform.py` | 23 | 18 | 6 | 0 | 17% |
| `adapters/tms/evidence.py` | 48 | 36 | 12 | 0 | 20% |
| `config.py` | 13 | 9 | 6 | 0 | 21% |
| `adapters/twin/client.py` | 54 | 39 | 8 | 0 | 24% |
| `adapters/fmcsa/client.py` | 113 | 72 | 52 | 7 | 29% |
| `scripts/configure_workflow.py` | 91 | 61 | 28 | 1 | 33% |
| `adapters/notify/email.py` | 20 | 13 | 0 | 0 | 35% |
| `api/app.py` | 238 | 100 | 62 | 14 | 54% |
| `adapters/twin/repository.py` | 201 | 77 | 82 | 18 | 58% |
| `adapters/twin/bookings.py` | 129 | 26 | 64 | 17 | 75% |
| `core/calls.py` | 377 | 69 | 168 | 45 | 79% |
| `adapters/tms/client.py` | 194 | 22 | 76 | 7 | 88% |
| `core/booking.py` | 206 | 20 | 64 | 9 | 89% |
| `adapters/confirmation.py` | 100 | 7 | 42 | 5 | 92% |
| `adapters/tms/fake.py` | 145 | 8 | 44 | 6 | 93% |
| `adapters/transcripts.py` | 85 | 4 | 38 | 3 | 94% |
| `adapters/tms/mapping.py` | 35 | 1 | 6 | 1 | 95% |
| `core/pricing.py` | 53 | 1 | 10 | 1 | 97% |
| `adapters/tms/protocol.py`, `core/inventory.py`, `loads.py`, `models.py`, `money.py`, `negotiation.py`, `ports.py` | | 0 | | 0 | 100% |
| **TOTAL** | **2317** | **583** | **824** | **134** | **72%** |

Excluding `scripts/` and `fake.py`: 73%. For comparison, `main` has 112 passing tests at 96%. Coverage fell by 24 points as the system was added, so the newest code is the least tested.

Tests per file: `test_booking` 46, `test_client` 27, `test_runtime` 27, `test_protocol` 20, `test_pricing` 19, `test_confirmation` 13, `test_entity_storage` 10, `test_transcripts` 9, `test_confirmation_adapter` 4, `test_invariants` 4, `test_workflow_contract` 4, `test_workflow_configuration` 3, `test_fmcsa_policy` 1.

Uncovered lines that matter most:

| Lines | What never ran offline |
|---|---|
| `adapters/twin/bookings.py:124,166-169,179` | Live consent and verification guards at reservation and at intent |
| `adapters/twin/bookings.py:83-86,88-89,101-102` | Lost call-claim and lost load-claim paths |
| `adapters/twin/repository.py:91-99` | Production `defer_aux`, the audit write path |
| `adapters/twin/repository.py:216-225,228-233,240-253,256-271,274-282,285-293` | All Twin SQL except `get` |
| `api/app.py:98-121` | Startup recovery, sweep, shutdown |
| `api/app.py:269-272,276-279,291-319` | `POST /bookings`, close, rep actions. Tests reach these routes only to assert auth rejection (`test_runtime.py:222-241`) |
| `core/booking.py:238-251` | Receipt save retry and fallback log |

`TwinRepository` is constructed once in all tests, to prove a corrupt row raises (`test_invariants.py:22`). `live=True` is used once (`test_invariants.py:26`).

### 2.3 ruff

No ruff configuration is committed, so these are tool defaults.

| Command | Result |
|---|---|
| `ruff check service` | **98 errors**, 64 auto-fixable: 79 production, 19 tests |
| Production by rule | I001 22, FURB167 16, BLE001 14, B023 9, UP017 5, F401 4, S110 3, TRY004 2, SIM102 1, FURB162 1, S112 1, F841 1 |
| `ruff check service --select F` | **12 errors**: 5 production (`twin/bookings.py:10`, `api/app.py:21`, `core/booking.py:19`, `scripts/configure_workflow.py:123`, `scripts/fly_session.py:5`), 7 tests |
| `ruff check service --exclude service/tests --select E,F,W,I,B,C90,N,UP,S,BLE,ANN,A,ARG,C4,PIE,PL,RET,SIM,TRY,ERA,RUF --statistics` | **1082 errors**: ANN family 578, E501 194, TRY003 111, PLR2004 32, I001 22, C901 14, BLE001 14, S608 10, other 107 |
| `ruff format --check service` | 39 of 56 files would change at the default 88 columns |
| `ruff format --check --line-length 100 service` | 6 of 56 files would change. The code is written to 100 columns but nothing records that. |

I checked the B023 findings: none is a live bug, because each closure runs inside its own loop iteration.

### 2.4 mypy

| Command | Result |
|---|---|
| `mypy --strict service` | **1375 errors in 47 files** (55 checked) |
| `mypy --strict --exclude service/tests service` | **587 errors in 32 files** (40 checked) |
| `mypy --exclude service/tests service` | `Success: no issues found in 40 source files` |

Default mode passes only because mypy skips the bodies of unannotated functions, and **7 of 235 production functions are fully annotated**. A green default run proves almost nothing here.

Production errors by code: no-untyped-call 322, no-untyped-def 229, type-arg 13, attr-defined 10, var-annotated 6, union-attr 4, arg-type 2, assignment 1.
Top files: `core/calls.py` 100, `twin/repository.py` 66, `api/app.py` 58, `core/booking.py` 41, `tms/client.py` 35, `scripts/configure_workflow.py` 33, `twin/bookings.py` 32, `fmcsa/client.py` 29. On `main` the figure is 150 errors in 10 files.

### 2.5 radon

`radon cc service -s -a --exclude 'service/tests/*'`: 219 blocks, average A (4.76). Ranks: A 159, B 33, C 23, D 3, E 1, F 0.

The average flatters the code, because the risk sits in a few blocks:

| Block | Rank (CC) |
|---|---|
| `adapters/transcripts.py:53 redact_transcript` | E (40) |
| `adapters/confirmation.py:35 consent_evidence` | D (29) |
| `scripts/migrate_twin_rows.py:20 migrate` | D (28) |
| `api/app.py:27 make_app.collect` (`--show-closures`) | D (23) |
| `core/calls.py:502 Runtime.book` | D (22) |
| `core/calls.py:632 Runtime.snapshot` | C (20) |
| `adapters/confirmation.py:111 NativeConfirmation.__call__` | C (19) |
| `adapters/fmcsa/client.py:90 FMCSAClient.assess` | C (19) |
| `adapters/tms/protocol.py:86 parse_reply` | C (18) |
| `adapters/twin/bookings.py:62 TwinBookingStore.create` | C (18) |
| `core/booking.py:190 BookingService._submit` | C (16) |

`radon mi service -s`: `core/calls.py` **C (6.47)**, `twin/repository.py` B (15.28), `tms/client.py` B (18.40), `core/booking.py` A (24.41), `transcripts.py` A (27.46), `api/app.py` A (27.62), `twin/bookings.py` A (29.37). All others are A, above 34.

`radon raw`: production LOC 4501, SLOC 3857, 31 comment lines (1%), 509 blank. Tests LOC 2456, SLOC 2099.

Longest functions: `make_app` 335 lines, `configure_workflow.main` 230, `Runtime.book` 105, `validate_twin.main` 96, `redact_transcript` 86, `TwinBookingStore.create` 79, `migrate` 77. `Runtime` has 18 methods.

### 2.6 Other tools

| Check | Result |
|---|---|
| `bandit -r service -x service/tests` | High 0, Medium 13, Low 23. Mediums: 9 string-built SQL, 2 `urlopen`, 1 `/tmp` path, 1 bind to all interfaces |
| `vulture service --exclude service/tests --min-confidence 60` | Confirmed unused: `retryable` (`fmcsa/client.py:14`), `run_id` (`notify/email.py:13`), `persistence_pending`, `TmsPort`, `initialize` |
| `pip-audit -r requirements.txt` | `starlette 0.49.3`: 5 advisories (PYSEC-2026-161, -248, -249, -2280, -2281), fixed from 1.0.1 to 1.3.1. Nothing else flagged. Exploitability not assessed. |
| `npm audit --omit=dev` (`ops-app`) | 27: 2 low, 9 moderate, 14 high, 2 critical. Critical: `next` (direct, 16.1.6 pinned), `proxy-addr` (transitive). Exploitability not assessed. |
| `npm audit` (all) | 42: 2 low, 24 moderate, 14 high, 2 critical |
| `docker build` | Passes, 52.4 MB, runs as uid 10001 on Python 3.12.14. Image contains `service/tests/`, `service/scripts/` and `tms/fake.py`. With no config and no network it exits with `RuntimeError`, which fails closed. |
| `next build`, then `tsc --noEmit` (Node 22 container) | Both pass. The build needs network for a Google Font. |
| `eslint .` | Crashes in config validation, so the dashboard has no working lint. The app README admits this. |
| `ops-app` tests | 0 test files. 672 of 3304 source lines are project-written; the rest is template and UI kit. |
| CI, `pyproject.toml`, lint or type config, lockfile for Python | None exist |
| Secret-shaped scan of tracked files on `prototype/e2e` | No JWT, AWS, bearer, private-key, assigned-key or `webKey=` matches. Six matches on a four-word password pattern were ordinary English. No `.env` or `secrets/` path was ever committed on any branch. Exact-value matching was not done (section 9). |
| Personal email in tracked files | Appears in `PROJECT_GUIDE.md` and `Questions.Md` |

### 2.7 Structural checks

| Rule from the brief | Result |
|---|---|
| Business logic isolated from adapters | **Fails.** `core/calls.py:18` and `:123` import adapters. `core/calls.py:39` constructs `TwinBookingStore`. Rules live in adapters: consent and verification gates (`twin/bookings.py:113-124,165-179`), rep rules (`:185-194`), consent policy (`confirmation.py:35-104`), eligibility policy (`fmcsa/client.py:90-144`). Business logic lives in transport: transcript collection (`api/app.py:27-93`), QA relabelling (`:338-357`), rep audit (`:303-319`). |
| No environment reads inside logic | **Fails.** `core/calls.py:34,46,205,341` read a dict of the whole environment. `api/app.py:51` reads the workflow ID. |
| No hidden global state | **Fails.** `core/inventory.py:12` reads a file at import time. `tms/client.py:88` passes evidence through a `ContextVar`. `core/calls.py:37` loads the pricing file inside a constructor. |
| Explicit dependencies | **Partly.** A `clock` is injected, then bypassed at `core/booking.py:199`, `core/calls.py:379,393,445`, `twin/bookings.py:98,136,197`, `api/app.py:108`. |
| Literal code over clever abstraction | **Fails** in places. Production branches on test doubles and capabilities: `twin/bookings.py:224` `hasattr(repository, "data")`, `core/booking.py:228,318`, `api/app.py:300`. `core/calls.py:40,61` switch safety behaviour on `repository.label`. |
| Error handling | 14 `except Exception`, of which 13 drop the error with no log: `core/booking.py:246`, `core/calls.py:140,238,534,604`, `tms/client.py:121,242`, `twin/repository.py:94`, `api/app.py:90,112,214,226,335`. |
| Logging | **One** log statement in the service: `core/booking.py:251`. |
| State written but never read | `projection_errors` (`repository.py:38,95`), `latencies` (`twin/client.py:26,60`, unbounded list), `persistence_pending`. `invalidated_at` is read at `calls.py:277,303` and never written. Claim-row `write_intent_id` is always `None` at runtime (`bookings.py:58`), so its checks at `:157,:221` and `repository.py:103,280` do nothing. |
| `repository.drain()` | Only caller is a script (`scripts/validate_twin.py:94`). Production never drains. |

Evidence for what is sound:

- **One send.** `LOAD_BOOK` has one call site (`core/booking.py:231`). `TmsClient.book` has no retry loop, and `recover()` never sends.
- **Intent before send.** `core/booking.py:209` persists intent before `:231`.
- **Ceiling.** I ran a full call with a marked `MAX_BUY` value and searched every HTTP response and every stored row. The value and the field names appeared in neither.
- **Auth.** The middleware covers every path, including `/health` and unmatched routes (`api/app.py:125-139`), with a constant-time compare.
- **Framing.** `tms/protocol.py` has 100% branch coverage.
- **Pricing and rounds.** `core/negotiation.py` 100%, `core/pricing.py` 97%.
- **Call identity.** The workflow binds `run_id` from a platform variable, not a model argument (`scripts/configure_workflow.py:300`).

### 2.8 Trace of one request: `POST /bookings`, the send

This follows the real path from the tool call to the last stored row. `[n]` numbers Twin statements. `cas` means compare-and-set: write the row only if its version is unchanged. A claim is a row whose primary key can be taken only once, so it reserves a call or a load.

```text
Workflow tool request_booking
  POST /bookings  {"run_id": <platform variable>}        configure_workflow.py:300-312
api/app.py
  protect()         key check, 12 s deadline              :125-163
  book()            rejects rate, mc, load_id in body     :267-272
  execute()         validates run_id, per-call lock       :190-215
core/calls.py  Runtime.book                               :502
  read_call                                         [1]   repository.py:204  one UNION statement
  gate(), agreement present, mode check                   :512-524
  confirmation(...)  platform GET run, sessions, pages    confirmation.py:111  no Twin, not paced
  update_call(record)
    read_call                                       [2]
    cas calls                                       [3]   consent stored on the call row
    defer_aux call_events                           [+1]  fire and forget
core/booking.py  BookingService.request                   :166
twin/bookings.py  TwinBookingStore.create                 :62
    rows bookings by call                           [4]
    for_call: get claim                             [5]
    blocked_load_ids                                [6]
    acquire_claim call:<id>                         [7]
    acquire_claim load:<id>                         [8]   <-- claims held from here
    mutate calls (freeze): get, cas                 [9,10]  <-- a raise here leaks both claims
    cas bookings insert                             [11]  state AGREED
core/booking.py  _submit, as a shielded task              :190
    tms.get  LOAD_GET on a fresh TCP connection           up to 6 s of retries
    rechecks: OPEN, pickup, ceiling, deadline >= 6 s      :197-206
    store.update(SUBMITTING, write_intent_id)             twin/bookings.py:164
      live guard: get booking, get call             [12,13]
      mutate bookings: get, cas                     [14,15]  durable intent
    deadline >= 5 s, else FAILED but claims kept          :217-225
    tms.book  journal.begin (fsync), one send, 5 s limit  tms/client.py:216
    _record: update: get, cas                       [16,17]  reference saved
core/calls.py
  set_outcome: read_call, cas                       [18,19]  failure swallowed at :604
    defer_aux call_events                           [+1]
  agent_view()  -> {"status": "senior_review", ...}       core/booking.py:146
api/app.py  adds end_call_required
```

Result: **21 statements** on this path, 19 plus 2 audit writes, confirmed by the model in 2.10. Three rows change state with no transaction between them, which is why the ordering matters and why every gap below exists. A mid-level engineer cannot follow this in 60 seconds: it crosses five files, two nested closures adapted by `lambda state, call:` wrappers, and a shielded background task.

### 2.9 Reproductions

These use the real `make_app`, `Runtime`, `BookingService` and `TwinBookingStore`, the repository's `FakeTMS` on loopback, and `MemoryRepository` relabelled `LIVE` with production `defer_aux` restored. The Twin SQL layer is not involved, so these prove logic defects, not Twin behaviour.

| # | Scenario | Service said | Storage then held |
|---|---|---|---|
| S1 | `call_events` insert fails, rep confirms | `rep_decision: confirmed`, `status: ok` | Booking confirmed. **No `rep_confirm` event.** `projection_errors` 3, and that counter is absent from `/ops/snapshot`. |
| S2 | Lifespan exits with audit writes queued | Nothing | 7 queued writes, 0 events persisted. Shutdown awaits only `bookings.pending`. |
| S3 | Carrier hangs up during consent read | `close`: `ended_without_booking`; `/bookings`: `booking_failed` | 0 sends, 0 booking rows, `load:LD1` claim `active: true`. Dashboard queue empty. `recover()` after restart finds 0. **Load still blocked after restart; next carrier gets `no_match`.** |
| S4 | Hang-up between reservation and intent | `booking_failed` | 0 sends. Row stuck `AGREED`, claims active, no dashboard action, until a process restart turns it `FAILED`. |
| S5 | Twin write fails after a real send | `senior_review`, call outcome `agreed_pending_rep` | 1 send. Row `SUBMITTING`, reference `null`, no retry. After restart with the journal gone: `UNKNOWN`, reference `null`. The reference survives only in a stderr log line. |
| S6 | Second close 60 s after the first | `closed` twice | `closed_at` moved from 1000.0 to 1060.0, 2 close events. |

S3 and S4 are reachable because `POST /calls/{id}/close` bypasses the per-call lock (`api/app.py:274-279`), and the workflow's post-call node fires it when a carrier hangs up. The scripts are not in this folder, because the brief allows one new file. Each row is specific enough to rebuild as a test, which is step 3 in section 7.

### 2.10 Statement budget and concurrency

Every row operation below passes through the real `Platform.sql` pacing code (4 starts per second, 4 in flight). Only the HTTP request inside it is stubbed, at a fixed 100 ms. TMS is the loopback fake and FMCSA and SMTP are instant stubs, which flatters the service. Consent adds a fixed 0.45 s for its three platform reads.

**One call, nothing else running:**

| Endpoint | Statements | Seconds |
|---|---:|---:|
| `POST /carriers/verify` | 5 | 0.62 |
| `POST /otp/send` | 13 | 3.02 |
| `POST /otp/verify` | 7 | 1.76 |
| `POST /loads/search` | 6 | 1.21 |
| `POST /negotiate`, counter | 6 | 1.01 |
| `POST /negotiate`, accept | 5 | 1.01 |
| `POST /bookings`, permission | 4 | 1.07 |
| `POST /bookings`, send | **21** | **5.34** |
| `POST /calls/{id}/close` | 3 | 0.51 |
| **Voice call total** | **70** | **15.6** |
| `GET /ops/snapshot` | 9 | 2.27 |
| `POST /bookings/{id}/confirm` | 5 | 1.27 |

The 21 matches the trace in 2.8 (19 plus 2 audit writes). The 15 statements before `LOAD_BOOK` match the project's own `candidate-booking-budget.json`. Of the 70, 13 are audit writes (19%). At 4 per second the absolute ceiling is about 3.4 full calls per minute with nothing else on the queue.

**Two calls reaching `/bookings` close together, no other traffic:**

| Gap | Responses | Sends | Outcome |
|---|---|---:|---|
| 0 s | `not_booked`, `not_booked` | 0 | **LD0: `FAILED`, intent set, claim active, `send_started=False`, so blocked forever with nothing sent.** LD1 failed before intent and was released. |
| 2 s | `senior_review`, `not_booked` | 1 | Second load blocked forever with nothing sent |
| 4 s, 6 s, 8 s | Both `senior_review` | 2 | Both fine |

**One call, while a rep uses the dashboard.** A rep action in `ops-app` costs two snapshots: the route's pre-check, then `router.refresh()`.

| Concurrent snapshots | Response | Sends | Row |
|---|---|---:|---|
| 1 | `senior_review` | 1 | `ACK_PENDING` |
| 2 | `not_booked` | 0 | `FAILED`, `deadline_before_send`, released |
| 3 | `in_progress` | 0 | `FAILED`, `deadline_before_send`, released |
| 4 | `in_progress` | 0 | `FAILED`, `deadline_before_send`, released |

So **one rep action during a booking can fail that booking**. A failed booking cannot be retried on the same agreement, because `create` replays the recorded operation (`twin/bookings.py:64-68`).

**Calls with human pauses.** This is the most realistic view. Each scenario ran in its own process with 3 seeds. Calls start at random within 240 s, and 8 tool calls with pauses of 20 to 40 s make each call about 4 minutes. "Burned" means `FAILED` with intent set: blocked forever with nothing sent.

| Calls in the 4-minute window | Booked, no rep activity | Burned | Booked, one rep action a minute | Burned |
|---:|---:|---:|---:|---:|
| 3 | 9 of 9 | 0 | 8 of 9 | 0 |
| 5 | 13 of 15 | 0 | 9 of 15 | 1 |
| 8 | 19 of 24 | 2 | 17 of 24 | 3 |
| 12 | 19 of 36 | 5 | 18 of 36 | 2 |

The same model compressed into a 90-second window with 6 to 14 s pauses booked 10 of 12 at 4 calls, 5 of 12 at 4 calls with a rep action every 15 s, and 7 of 24 at 8 calls.

All 82 failed bookings across these 33 runs had the reason `deadline_before_send`, and no run sent more than once per call. So the service fails closed under load, which is the right direction, but 13 of the 168 modelled 4-minute calls ended with a load burned. The small samples mean these show the shape, not a precise limit. An earlier run with all scenarios in one process was discarded, because sharing a process overstated failure.

**No pauses at all, as a stress limit only.** Back-to-back requests overstate contention, so this is not a forecast: 1 call booked 1 of 1, while 2, 3, 4, 6 and 8 simultaneous calls booked 0. In those runs the test transport waits for all server work, so times past 12 s are server work. A real server answers the agent `in_progress` at 12 s and carries on.

The `ops-app` dashboard does not poll. It loads a snapshot on page view and after each action, so rep activity is bounded by what reps do.

## 3. Top 10 problems, most serious first

### 1. The system is not on `main` or on any remote

- **Where:** `service/README.md:3` on `main`; branch `prototype/e2e`, 23 commits ahead of `main`, no upstream. `main` is 8 commits ahead of `origin/main`.
- **Why it matters:** the PDF requires a repository link. Today that link would show no service, no dashboard and no workflow. One disk failure loses the only working version.
- **Smallest fix:** the merge base is `main`'s tip, so this is a fast-forward. Fast-forward `main` to `4b5ef3a`, then push to the private remote, under the existing review and owner-approval rule. This reverses the earlier note that `main` alone is production, so it is the owner's decision.

### 2. A hang-up can remove a load from sale permanently, with no trace

- **Where:** `service/adapters/twin/bookings.py:82-130`, `service/api/app.py:274-279`, `service/core/booking.py:209`, `service/core/calls.py:599`.
- **Why it matters:** `create()` takes both claims, then `freeze` raises if the call has closed or verification has lapsed. Nothing releases the claims. No booking row exists, so the dashboard shows nothing, and `recover()` scans only booking rows, so a restart cannot fix it. S3 shows the next carrier getting `no_match` on a load that was never sent. A carrier saying yes and hanging up is ordinary behaviour. In production this is freight that silently stops being offered, and nobody is told. S4 is the sibling: the raise at intent leaves a row stuck in `AGREED` until a restart.
- **Smallest fix:** wrap `freeze` and call `release()` on `BookingConflict`, about 4 lines. In `_submit`, catch the raise and call `_fail`. Take `runtime.locks[cid]` in the close route, about 2 lines. Then add an orphan reaper to `sweep`. It is provably safe: the booking row is written before intent, so a claim with no booking row can never have been sent.

### 3. A real booking receipt can be lost after the send

- **Where:** `service/core/booking.py:234-274`, `service/adapters/tms/evidence.py:3-4`, `fly.toml` (no `[mounts]`).
- **Why it matters:** `_record` retries three times within 0.15 s, then only logs. The carrier hears `senior_review` and the call records `agreed_pending_rep`, while the row stays `SUBMITTING` with no reference and no dashboard action (S5). The fallback journal lives in `/tmp` on a machine that auto-stops. TMS reads never return the reference, so once the log line ages out it cannot be recovered. There is no cancel to undo the booking.
- **Smallest fix:** keep unsaved receipts in a bounded in-process list and retry them from `sweep`, using the existing `_record_once`. Show `SUBMITTING` older than two minutes on the dashboard with a Reconcile action. A Fly volume would close the restart gap, but the recorded budget rule forbids one, so that is an owner decision.

### 4. Audit records can disagree with state, and nobody would know

- **Where:** `service/adapters/twin/repository.py:90-99`, `service/api/app.py:117-121,303-319`, `service/core/calls.py:618-630`, `service/core/booking.py` (no event call at all).
- **Why it matters:** "no audit trail" is one of the five problems the PDF names, and it requires all call activity in Twin. Events are fire-and-forget after the state commit. S1 shows a rep confirmation with no event. S2 shows shutdown abandoning queued writes. The only signal is a counter nothing reads. Booking state transitions emit no events, so a booking's history is overwritten in place. Section 5 lists seven ways the records diverge.
- **Smallest fix:** first, `await runtime.repository.drain()` in shutdown and expose `projection_errors` on `/ops/snapshot`, about 3 lines. The real fix is the row-embedded history in section 5.

### 5. Capacity is one shared queue, and overload burns inventory

- **Where:** `service/adapters/twin/client.py:27-29,63-77`, `service/core/booking.py:217-225`, `service/adapters/twin/repository.py:107-111`, `service/core/calls.py:632`.
- **Why it matters:** voice calls, the dashboard and the sweep share one 4-per-second queue with no priority. A booking needs 15 statements before it can send, and must pass deadline checks 6 s and 7 s into its 12 s budget. In the model in 2.10, two bookings starting together sent nothing, one rep action during a booking failed it, and with 4-minute calls, 5 calls in a window booked 13 of 15, falling to 9 of 15 with one rep action a minute. At 12 calls about half booked. The PDF's core complaint is peak-hour overload. The failure path is worse than a timeout: once intent is saved and the deadline check at `:217` fails, the row goes `FAILED` with `write_intent_id` still set, so the load stays blocked forever although the code itself recorded `send_started: False`.
- **Smallest fix:** clear `write_intent_id` in that one update, since the same coroutine proves no send began. That needs an owner decision, because it narrows the recorded rule that every past intent blocks. Then remove repeated reads, cache the snapshot, and give voice statements priority.

### 6. Business logic is not isolated, and two files fail the 60-second rule

- **Where:** `service/core/calls.py:18,39,123`, `service/adapters/twin/bookings.py:113-124,165-179,185-194`, `service/api/app.py:26-360`.
- **Why it matters:** `core` imports the Twin adapter, so the domain cannot be tested or reasoned about without storage. Consent gating sits in a storage adapter, so changing the rule means editing persistence code. `InMemoryBookingStore` (`core/booking.py:96-143`) restates the rep rules a second time. `calls.py` is 704 lines with maintainability index 6.47, the only module ranked C. `make_app` is one 335-line closure holding routing, auth, audit and transcript collection. The owner must defend every file, and these two cannot be defended quickly.
- **Smallest fix:** inject `booking_store` and `normalize_mc` into `Runtime`, which removes both imports. Move the gates into `core/booking.py`. The file splits follow in section 7.

### 7. The tests skip the paths that carry the most risk

- **Where:** `service/adapters/twin/repository.py:173-174`, `service/adapters/twin/bookings.py:224`, `service/core/calls.py:40,61`, `service/tests/test_runtime.py:118`.
- **Why it matters:** the 187 passing tests sound stronger than they are. `MemoryRepository.defer_aux` replaces the async audit write with a synchronous one, so audit failure is untestable as built. Consent gates run only when `label == "LIVE"`, and the test double is labelled `SIMULATED`. Tests set `cohort = "real"` by writing directly into the store. All Twin SQL except `get` never executes offline. `POST /bookings`, close and rep actions are never exercised successfully over HTTP. The suite is green while all six defects in 2.9 exist.
- **Smallest fix:** make `live` an explicit constructor argument, delete the `defer_aux` override, and add a fake SQL client that records statements so the real `TwinRepository` runs offline. Port S1 to S6 as tests.

### 8. There is no type contract

- **Where:** `service/core/calls.py` throughout, `service/core/ports.py:31-36`, `service/core/booking.py:76-93`.
- **Why it matters:** 7 of 235 functions are annotated, and the central object is an untyped dict accessed by string key, so a typo becomes `KeyError`. `api/app.py:165-168` then turns any `KeyError` or `ValueError` into HTTP 400, which reports server bugs as client errors. The protocols are decoration: `TmsPort` is unused and has the wrong `book` signature, and `BookingStore` omits `for_call` and misdeclares `blocked_load_ids`. `decode` (`twin/bookings.py:25-29`) silently drops unknown fields.
- **Smallest fix:** add a `Call` dataclass with one `from_row` and `to_row`, make the two protocols true, and ratchet mypy file by file.

### 9. Failures are silent in production

- **Where:** `service/api/app.py:112-113,90-91`, `service/core/calls.py:604-605`, `service/core/booking.py:246-247`, `fly.toml:21`.
- **Why it matters:** there is one log statement in the whole service. The sweep swallows every exception with `pass`, so if it breaks, stale calls and transcripts stop quietly. There are no request IDs and no metrics, and the platform health check is TCP only. Each failure in problems 2 to 5 would be invisible in production, and that is why they went unseen.
- **Smallest fix:** one structured `log_event` helper, called in the 13 silent handlers and on each booking transition, with a test asserting no secrets appear.

### 10. Deployment is tied to one Mac and one lab, and dependencies are unpatched

- **Where:** `service/scripts/deploy.py:9-10,23`, `service/scripts/configure_workflow.py:8-10`, `Makefile:2-4`, `fly.toml:1`, `ops-app/src/lib/ops-service.ts:9`, `Dockerfile:5`, `requirements.txt`, `ops-app/package.json`.
- **Why it matters:** the PDF requires single-command deployment to a cloud of the customer's choice. The Fly app name is hard-coded in three files and its host in two more, the deploy script assumes `/Applications/Docker.app`, and the Makefile assumes `secrets/venv`. Lab names such as `codex-e2e-lab-sg-20261031`, `isolated-fde-harness/1` and `PROTOTYPE_WORKFLOW_ID` would read badly in a review. The image ships tests that patch `socket` on import, although the README warns never to import them live. `next` has a critical advisory, and `ops-app` lint does not run. `ops-app/README.md` also states that the deployed App is older than the repository source. OTP email goes to one configured inbox (`notify/email.py:18`), which the project records as approved demo scope, but it is not the PDF's carrier email or SMS.
- **Smallest fix:** read app, host and workflow IDs from settings. Copy only runtime packages into the image. Upgrade `fastapi` and `next` and rerun tests. State the OTP scope in the build description.

## 4. File table for `service/`

Sizes are lines now, then the approximate target. A size with `->` marks a file split or moved.

| File | Lines | Verdict | Reason | Target |
|---|---:|---|---|---:|
| `README.md` | 102 | Refactor | Accurate, but mixes run notes and evidence; add a module map | 80 |
| `__init__.py` and 7 other empty or one-line `__init__.py` | 0-1 | Keep | Package markers | 0 |
| `config.py` | 18 | Rewrite | Untyped dict of the whole environment; becomes a typed frozen `Settings` and the only env reader | 70 |
| `api/app.py` | 403 | Rewrite | 335-line closure; holds logic that belongs elsewhere | 70 + routes |
| `adapters/confirmation.py` | 155 | Refactor | Pure consent policy mixed with HTTP paging; CC 29 and 19 | 40, -> `core/consent.py` 110 |
| `adapters/transcripts.py` | 138 | Refactor | Pure redaction misplaced; CC 40 is the worst block in the repo | -> `core/redaction.py` 110 |
| `adapters/fmcsa/client.py` | 197 | Refactor | Eligibility policy mixed with HTTP; exception extends `TmsUnavailable`; lab user agent | 90, -> `core/carrier_policy.py` 70 |
| `adapters/notify/email.py` | 30 | Refactor | Takes the whole env dict; hard-coded SMTP host; unused parameters | 35 |
| `adapters/tms/protocol.py` | 120 | Keep | 100% branch coverage, no I/O, clear rules | 120 |
| `adapters/tms/mapping.py` | 78 | Keep | One mapping, 95% covered | 78 |
| `adapters/tms/client.py` | 289 | Refactor | Sound behaviour; replace `ContextVar` with an explicit argument, move the local import | 240 |
| `adapters/tms/evidence.py` | 70 | Keep | Clear single job; only add tests, now 20% | 70 |
| `adapters/tms/fake.py` | 214 | Keep, move | Test double in a production package, shipped in the image | -> `tests/fakes/fake_tms.py` 214 |
| `adapters/twin/client.py` | 77 | Refactor | Sound pacing; remove `latencies`, add voice priority, take explicit settings | 90 |
| `adapters/twin/repository.py` | 293 | Refactor | Base plus test double in one file; add history flush; remove `defer_aux` | 200, -> `tests/fakes/memory_repository.py` 70 |
| `adapters/twin/bookings.py` | 231 | Refactor | Business gates in storage; leaks claims; test-double branch | 150 |
| `core/booking.py` | 398 | Refactor | State machine is good; remove `InMemoryBookingStore`, duck typing and logging | 280 |
| `core/calls.py` | 704 | Refactor | God class, MI 6.47, imports adapters | -> `flows/` about 520 |
| `core/inventory.py` | 12 | Refactor | Import-time file read; load at startup and inject | 12 |
| `core/loads.py` | 28 | Keep | Pure, 100% | 28 |
| `core/models.py` | 48 | Keep | Typed, pure | 48 |
| `core/money.py` | 20 | Keep | Pure, 100% | 20 |
| `core/negotiation.py` | 41 | Keep | Pure, 100%, enforces three rounds | 41 |
| `core/ports.py` | 36 | Refactor | Protocols do not match reality; `BookingStore` moves here | 80 |
| `core/pricing.py` | 88 | Keep | Pure, 97%. CC 11 is acceptable for its job | 88 |
| `policy/pricing-v1.json` | 7 | Keep | Versioned policy | 7 |
| `policy/blocked-loads-v1.json` | 21 | Keep | Explicit inventory exclusions | 21 |
| `scripts/cli_platform.py` | 35 | Delete | Subclass running `asyncio.run` per request; drop once `Platform` uses httpx | 0 |
| `scripts/configure_workflow.py` | 339 | Refactor | 230-line `main`, hard-coded IDs and host; split per node type | 200 |
| `scripts/deploy.py` | 41 | Refactor | Mac path and fixed app; read settings | 30 |
| `scripts/export_workflow.py` | 47 | Keep | Read-only; IDs come from settings after the change above | 45 |
| `scripts/fly_session.py` | 51 | Refactor | Unused import, fixed app name | 45 |
| `scripts/migrate_twin_rows.py` | 108 | Delete | One-shot cutover that refuses to run twice; git history keeps it | 0 |
| `scripts/provision_twin.py` | 19 | Refactor | Name is false: it only checks access. Rename `check_twin.py` | 19 |
| `scripts/set_email_credential.py` | 41 | Keep | Owner-only prompt, small, clear | 41 |
| `scripts/validate_twin.py` | 129 | Refactor | Useful live probe; rename `probe_twin_contention.py`, keep out of the image | 100 |
| `tests/__init__.py` | 3 | Keep | Installs the network guard | 3 |
| `tests/support.py` | 34 | Keep | Small helpers | 40 |
| `tests/test_booking.py` | 512 | Keep | Strong state-machine tests; add S2, S4, S5 | 600 |
| `tests/test_client.py` | 260 | Keep | Real TCP fault injection | 260 |
| `tests/test_confirmation.py` | 200 | Keep | Good cases; follows consent to core | 200 |
| `tests/test_confirmation_adapter.py` | 76 | Keep | Paging contract | 76 |
| `tests/test_entity_storage.py` | 149 | Refactor | Good contention tests; add S3 and run against the SQL fake | 220 |
| `tests/test_fmcsa_policy.py` | 20 | Refactor | One test for CC 19 logic; add a table of cases | 120 |
| `tests/test_invariants.py` | 97 | Keep | Add crash-point test here | 200 |
| `tests/test_pricing.py` | 148 | Keep | Property style, good | 148 |
| `tests/test_protocol.py` | 213 | Keep | Fixture-driven | 213 |
| `tests/test_runtime.py` | 498 | Refactor | Writes into the store; make HTTP-first and add booking, close, rep routes | 650 |
| `tests/test_transcripts.py` | 131 | Keep | Redaction cases | 131 |
| `tests/test_workflow_configuration.py` | 53 | Keep | Static contract | 53 |
| `tests/test_workflow_contract.py` | 62 | Keep | Static contract | 62 |

Totals: production about 4,500 lines now, including the 214-line fake, and about 3,600 target. Fewer lines is not the goal; the gain is that no function exceeds 50 lines and every file has one job.

## 5. Proposed design

### 5.1 Storage assessment

**Can audit records disagree with call state? Yes.** Seven ways, all from the code:

| # | Divergence | Evidence |
|---|---|---|
| D1 | Audit insert fails after state commits | S1, `repository.py:90-95` |
| D2 | Process stops with audit writes queued | S2, `app.py:117-121` |
| D3 | Booking transitions have no events, and the row is overwritten, so no history exists | `core/booking.py` has no event call |
| D4 | Call outcome and booking state are separate rows updated at separate times | S3, S4, S5; `calls.py:601-605,618-630` |
| D5 | `close` reads `bookings[-1]`, but `read_call` has no `ORDER BY` | `calls.py:621`, `repository.py:209-215` |
| D6 | `closed_at` is overwritten on repeat close | S6, `calls.py:624` |
| D7 | QA relabelling rewrites `cohort` and emits no event | `app.py:351-352` |

Rows that must not diverge do hold up. Each row's own update is a compare-and-set in one statement, and call and load claims are primary-key guarded. That part of the design should stay: the project's evidence shows one winner in each contention probe, and the brief records 1 winner of 20.

**Options compared.** Statement figures are per voice call, from 2.10.

| | A. Today | B. History in the row (recommended) | C. Event log as source of truth | D. One SQL statement across tables | E. External Postgres |
|---|---|---|---|---|---|
| How it works | State CAS, then best-effort inserts | Event appended to the same row in the same CAS; `call_events` is rebuilt from it | Insert `call_id:seq` by primary key; state is computed by replaying events | A CTE, one SQL statement that writes two tables, updates the row and inserts the event together | Real transactions |
| Audit can lose an event | Yes | No, it commits with the state | No | No, if allowed | No |
| Cross-row divergence | Yes | Removed for outcome by deriving it | Yes, between call and booking logs | Reduced | No |
| Uses only verified Twin behaviour | Yes | Yes: single-row CAS, primary-key insert | Yes | **Unverified.** The brief says no multi-table transactions; a CTE may be rejected | Not Twin |
| Twin statements | 70 | About 58: the 13 audit writes ride in the CAS, plus 1 flush | About the same as B | About the same as B | None on Twin |
| Code change | None | About 150 lines, 4 files | Rewrite of `calls.py`, `bookings.py`, migration of live rows | Small, but all SQL becomes bespoke | New service, secrets, deploy, backups |
| Dashboard query | Direct rows | Direct rows; `call_events` may lag seconds, never lose | Needs projections, reintroducing lag | Direct rows | Direct rows |
| PDF fit | Weak on audit | Strong, Twin native | Strong, Twin native | Strong if allowed | Weak: needs justification, and B shows Twin can do it |
| Main risk | Silent audit loss | Row growth; must trim after flush | Largest rewrite, cannot be proven without live calls | May not exist | Cost, and the USD 3 budget |

**Recommendation: B, plus derived outcome.**

- `Call` and `Booking` rows each gain an ordered `history` list. Every state change appends to it inside the existing `update_call` or `mutate`, so event and state commit in one statement. D1, D2, D3 and D7 end by construction, and a rep decision cannot exist without its event.
- A flush writes `call_events` with deterministic IDs (`call:<id>:<seq>`, `booking:<id>:<seq>`) using one multi-row `INSERT ... ON CONFLICT DO NOTHING`. It runs at close, in the sweep and at startup, so it is safe to repeat. `call_events` becomes a query surface and can be rebuilt.
- Call outcome stops being stored for booked calls. `effective_outcome(call, booking)` computes it at read time. D4 and D5 end, because there is one source for each fact. `closed_at` is set once, which ends D6.
- The dashboard shows `history` length against `call_events` count per call, so lag is visible.
- Option D is worth one probe on synthetic rows, because if Twin accepts a CTE it would simplify the flush. Nothing here depends on it.

### 5.2 Directory tree

```text
service/
  config.py                 Settings dataclass; the only module that reads the environment
  bootstrap.py              Composition root: builds adapters, injects them, returns the app
  api/
    app.py                  create_app: middleware, error mapping, lifespan
    auth.py                 Key check for agent and ops routes
    agent_routes.py         Thin routes for voice tools
    ops_routes.py           Thin routes for the dashboard
    schemas.py              Request models, one per route
  flows/                    One use case per file; orchestrates ports; no SQL, no sockets
    carrier_check.py        verify_carrier
    code_check.py           send_code, verify_code
    offers.py               search
    rate_talks.py           negotiate
    booking_request.py      book
    closing.py              close, effective outcome
    operations_view.py      snapshot, rep actions
    transcripts.py          collect transcripts
    sweep.py                stale calls, stuck bookings, orphan claims, history flush
  core/                     Pure rules; imports nothing from flows, adapters or api
    call.py                 Call dataclass, gate(), history append
    booking.py              Booking, states, transitions, BookingService
    consent.py              consent_evidence
    carrier_policy.py       FMCSA eligibility decision
    redaction.py            Transcript redaction
    pricing.py  negotiation.py  money.py  loads.py  models.py
    inventory.py            Parses the blocked list passed in
    ports.py                TmsPort, BookingStore, CallStore, Notifier, DialogueSource
  adapters/
    tms/         protocol.py  mapping.py  client.py  evidence.py
    twin/        client.py  repository.py  bookings.py  history.py
    platform/    dialogue.py   One paging implementation, used by consent and transcripts
    fmcsa/       client.py
    notify/      email.py
  policy/        pricing-v1.json  blocked-loads-v1.json
  scripts/       configure_workflow.py  export_workflow.py  deploy.py  fly_session.py
                 check_twin.py  probe_twin_contention.py  set_email_credential.py
  tests/
    fakes/       fake_tms.py  memory_repository.py  fake_twin_sql.py
    test_*.py
```

### 5.3 Components

```text
 Carrier web call                       Rep in HappyRobot Apps
        |                                        |
        v                                        v
 +----------------+                   +----------------------+
 | HappyRobot     |                   | ops-app (Next.js)    |
 | voice workflow |                   | signed-in session    |
 +----------------+                   +----------------------+
        | tool calls + run_id                    | ops key, actor from session
        v                                        v
 +-----------------------------------------------------------+
 | api/      auth, schemas, thin routes, 12 s deadline       |
 +-----------------------------------------------------------+
        | plain arguments and typed results
        v
 +-----------------------------------------------------------+
 | flows/    one use case per file; per-call lock            |
 +-----------------------------------------------------------+
        | calls rules                | calls ports only
        v                            v
 +-------------------+     +---------------------------------+
 | core/             |<----| core/ports.py  (interfaces)     |
 | pure rules, no IO |     +---------------------------------+
 +-------------------+                ^ implemented by
                                      |
 +-----------+-----------+------------+---+-----------+
 | tms/      | twin/     | platform/      | fmcsa/    | notify/
 +-----------+-----------+----------------+-----------+
       |           |            |              |          |
       v           v            v              v          v
    TMS TCP   Twin SQL API  Runs and      FMCSA API    SMTP
       |           |        messages
       v           |
  Receipt journal  +-- calls, bookings, otp_challenges: CAS rows with history
                   +-- booking_claims: primary-key claims
                   +-- call_events etc: rebuilt from history, safe to repeat

 Dependency rule: api -> flows -> core <- adapters. bootstrap.py alone sees all.
```

## 6. Trade-offs

| Decision | Gain | Cost |
|---|---|---|
| Refactor, not rewrite | Keeps a proven path, 187 tests and hard-won TMS behaviour | Lives with some inherited shape; takes discipline to finish |
| History in the row | Audit cannot be lost; fewer statements; no new table | Larger rows; needs trimming; `call_events` can lag |
| Derived outcome | One source of truth | Call log query must read the booking too |
| Keep Twin | PDF-native, nothing to run | Stays near 4 statements per second; capacity remains bounded |
| Add a `flows/` layer | `core` becomes pure and readable | One more folder to learn |
| Typed `Call` dataclass | mypy can protect state | Conversion code; older rows need tolerant loading |
| Keep the exact-wording consent check | Conservative, never books on a vague answer | Brittle by design. It caused a redundant question on the passing call |

**Strongest argument against this verdict: do not touch the code at all.**

The deployed bytes passed a real end-to-end call, with hashes recorded in the evidence. No booking test can be undone, and refactoring invalidates that proof. Item 7 of this report says the offline suite misses the riskiest paths, so the safety net for a refactor is weakest exactly where the refactor would operate. A reviewer sees a working demo and a clear limits report. An honest prototype with documented gaps may score better than a late, restructured system that has never booked a load. On that reading, the right move is to fix only problems 1 to 4 and hand in.

I take this seriously, and it sets the order in section 7. Steps 0 to 5 are the defensible minimum, and each is small. The rest should stop if the deadline demands it. I still reject "touch nothing" for two reasons. First, S3 and S5 are real defects in code the owner must defend, and they are small to fix. Second, the owner has to explain every file, and a 704-line module with maintainability 6.47 and a 335-line closure cannot be explained. `BOOKING_MODE=rehearse` also weakens the argument: it runs a real call through to verified consent and sends nothing, so that part can be re-proven for free. It does stop before reservation, intent and send, so those steps can only be re-proven offline. That is exactly why steps 2 and 3 come first.

The opposite argument, a full rewrite, fails on evidence. `tms/protocol.py`, `mapping.py`, `negotiation.py`, `pricing.py` and the booking state machine are sound and tested. The defects are concentrated in about five files, and a rewrite would discard live-won knowledge with no way to re-prove it without spending loads.

## 7. Change order

One commit per row, following the project's writer and review workflow. Nothing is pushed without owner approval, and no step needs a live booking. "Trace" means the golden trace from step 2.

| # | Change | How behaviour is preserved | Verified by |
|---|---|---|---|
| 0 | Fast-forward `main` to `4b5ef3a`, push to the private remote | No file changes | Tree hash equal; 187 tests pass from a fresh clone |
| 1 | Add `pyproject.toml` (ruff at 100 columns, mypy, coverage), lockfile, CI in report-only mode. Run `ruff --fix` for imports only | Import order only | 187 tests; no behaviour diff |
| 2 | Add `fake_twin_sql.py` and a golden trace test: record exact SQL and TMS frames per endpoint on a scripted call | Tests only | Trace stable across two runs |
| 3 | Port S1 to S6 as tests marked expected-failure | Tests only | All six fail as documented |
| 4 | Fix S3, S4: release claims on conflict, `_fail` at intent, lock on close, orphan reaper in sweep | Happy path untouched | S3, S4 pass; trace unchanged on the happy path; 0 sends in failure tests |
| 5 | Fix S5 and drain: receipt retry in sweep, `drain()` in shutdown, expose counters, Reconcile for stuck rows. With owner approval, clear intent when the send never started | Adds retries; never adds a send | S2, S5 pass; assert `book_requests` stays at 1 |
| 6 | Add `log_event`, use it in the 13 silent handlers and on each transition | Logging only | Trace unchanged; test asserts no token, code or ceiling in logs |
| 7 | Owner rehearsal: one real call with `BOOKING_MODE=rehearse`. Covers everything up to verified consent, not reservation or send | Sends nothing | `rehearsal_complete` on the dashboard; 0 TMS sends |
| 8 | History in rows, flush, derived outcome | Old rows load with empty history; `call_events` rows keep their shape | Trace differs only as planned; S1 passes; randomized fault test finds 0 lost events |
| 9 | Reduce statements, priority queue, cached snapshot | Same writes, fewer repeat reads | Trace shows the planned removals; capacity gate |
| 10 | Remove core-to-adapter imports; inject store, clock, secrets; make `live` explicit | Wiring only | Trace unchanged; import test passes |
| 11 | Move consent, redaction and carrier policy to `core/`; share paging | Same functions and tests, new homes | Trace unchanged; moved tests pass untouched |
| 12 | Split `calls.py` into `flows/`, one file per commit | Moved code, same calls | Trace unchanged after each commit |
| 13 | Replace `make_app` with thin routes and `bootstrap.py`; add request schemas | Same paths, statuses and bodies | HTTP contract test from step 2 passes |
| 14 | Typed `Call`, true protocols, mypy strict file by file, starting at `core/` | Types only, plus `from_row` tolerance | Error count falls every commit, never rises |
| 15 | Move fakes to tests, slim the image, parameterise deploy, rename lab identifiers | Twin prefix stays configurable, so live rows still resolve | Image has no tests; `make deploy` runs from settings on a clean machine |
| 16 | Upgrade fastapi, starlette, next; repair `ops-app` lint; add tests for `ops-service.ts` | Dependency change alone in its own commit | Full suite, `next build`, `pip-audit`, `npm audit` |
| 17 | Owner rehearsal again, then decide with the owner whether one live send is worth a load | Rehearse sends nothing; a live send is an explicit owner decision | Same nine-item gate as the earlier run |

Stop after step 7 if time is short. That leaves the worst defects fixed, the code on `main`, and the structure unchanged but documented.

## 8. Measurable acceptance gates

Call it enterprise quality only when all of these pass in CI on `main`.

| Gate | Now | Target | Measured by |
|---|---|---:|---|
| Code on default branch and private remote | No | Yes | `git log origin/main` |
| Tests | 187 pass | All pass, none skipped | CI |
| Branch coverage, `core/` and `flows/` | 79% in `calls.py` | At least 95% | coverage per path |
| Branch coverage, `api/` | 54% | At least 90% | coverage |
| Branch coverage, `adapters/` | 24% to 100% | At least 85% each | coverage |
| Live-only code paths run offline | Almost none | 100% of guards | Coverage has no gap at the consent gates |
| Lint | 98 | 0 under the committed rule set | `ruff check` |
| Format | 6 files at 100 columns | 0 | `ruff format --check` |
| Types | 587 strict errors, 7 of 235 annotated | 0 production errors | `mypy --strict` |
| Function complexity | Max 40, 27 blocks at C or worse | Max 10; at most 3 named, justified exceptions | `radon cc -n C` |
| Maintainability | Min 6.47 | Every module at least 20 | `radon mi` |
| Size | 335-line function, 704-line module | Functions at most 50 lines, modules at most 300 | AST check in CI |
| Layering | 2 imports from core to adapters | 0 | Import test in CI |
| Environment reads | Spread through logic | Only `config.py` | Grep test |
| Wall clock | 8 bypasses | Only the injected clock | Grep test |
| Test code in production | `fake.py`, memory stores, `hasattr` on doubles | 0 | Grep test; image listing |
| Silent handlers | 13 of 14 | 0 | ruff BLE, S110, S112 enabled |
| Audit durability | Lossy | 0 lost events across 1,000 randomized fault runs | Fault test: each committed change has its event after flush |
| Crash safety | Partly tested | Crash at every statement index of the booking path gives at most 1 send, 0 orphan claims after reaper, 0 rows stuck past one sweep | Crash-point test |
| Double send | One call site | Still exactly one | Static test plus crash-point test |
| Ceiling secrecy | Passes | Value absent from every response, row and log in a full call | Marked-value test in CI |
| Twin statements before `LOAD_BOOK` | 15 | At most 10 | Golden trace |
| Statements per voice call | 70 | At most 50 | Golden trace |
| Capacity: 12 calls of about 4 minutes within a 4-minute window, one rep action a minute, 3 seeds | 18 of 36 booked, 2 loads burned | 36 of 36 booked, 0 burned, no response over 12 s | Load model on `fake_twin_sql` at 4 per second |
| Advisories | starlette 5; npm 2 critical, 14 high | 0 critical or high in production dependencies | `pip-audit`, `npm audit --omit=dev` |
| Dashboard lint and tests | Lint crashes, 0 tests | Lint passes; `ops-service.ts` at least 90% | CI |
| Deployment | Fixed Fly app on a Mac | One command, on a clean Linux runner, from settings only | CI dry run |
| Image | Includes tests and scripts | Runtime packages only | Image listing |
| Observability | 1 log statement | Every booking transition logged with call and booking IDs | Test on captured logs |
| Readability | Fails on 2 files | A mid-level engineer traces any endpoint in 60 seconds, checked on `/bookings` and `/otp/verify` | Timed walkthrough by someone new to the code |

## 9. What I could not verify

**Live behaviour.** No live system was contacted, by instruction.

- The Twin SQL strings themselves. `cas`, `acquire_claim`, `read_call` and the upserts have no offline execution, and their compare-and-set behaviour rests on evidence files from earlier agents plus the constraints in the brief. My reproductions replace that layer with memory.
- Whether Twin accepts parameter binding, multi-row inserts or a data-modifying CTE, and whether `standard_conforming_strings` is on. `literal()` at `twin/client.py:11` is safe only if it is. Option B's flush assumes a multi-row insert is accepted, and if not, it falls back to one insert per event, which costs statements but not safety.
- Twin's real limits and latency under load. The tables in 2.10 are a model: real pacing code, stubbed requests at 100 ms, an instant TMS, FMCSA and SMTP, which flatter the service, and assumed call lengths and rep activity. Absolute numbers will differ; the shape should hold.
- Whether the HappyRobot platform retries tool calls, its real tool timeout, or exactly when the post-call node fires relative to an in-flight tool. S3 and S4 assume close can land during `/bookings`. The code permits it, and the post-call node exists, but I did not observe it happen live.
- Fly behaviour: whether files survive stop and start. The code's own docstring and report call them ephemeral, and `fly.toml` has no mount. I did not test it. Log retention on Fly is also unknown, which decides how long the S5 fallback line survives.

**Claims taken from the repository, not re-proven.**

- The real call on run `5783608f-d54b-4a5d-b028-89db98ae10ec`, the hashes tying deployed bytes to `dd57d54`, the contention results and the QA results. I read the evidence files but cannot independently confirm them. All were produced by the agents that built the code. I did confirm that nothing under `service/`, `requirements.txt`, `Dockerfile` or `fly.toml` changed between `dd57d54` and `4b5ef3a`, so the audited code is the code those files describe.
- The brief's statements on 8 spent loads, 1 of 20 winners and the Apps gateway failure. `docs/platform-checks.md:9` records the 20-contender result and the evidence files record 1 of 8, but I could not re-run either.
- That the deployed workflow matches `happyrobot/prototype-workflow.json`, or that the deployed App matches `ops-app/`. The app README says the deployed one is older.
- Whether the App's cookie and callback flow is safe. It is platform template code. I read it but did not test it, and `app/callback/route.ts` accepts tokens in the URL.

**Not done.**

- `.env` and `secrets/` were not opened, so the secret scan used patterns only, not exact values. A real credential in an unusual format could still be in tracked evidence.
- The 95 evidence files were sampled, not read in full. The voice QA outputs were not re-judged.
- Prompt quality, voice behaviour and adversarial resistance of the model. The PDF's QA requirement was checked only for the presence of artifacts.
- Exploitability of the dependency advisories.
- The Luke question on `PENDING` semantics stays open, so whether `ACK_PENDING` is the right final state for a demo is unresolved.
- `lab/harness-v24` was listed but not audited. It predates the prototype.
