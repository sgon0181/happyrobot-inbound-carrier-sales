# Audit report: corrected scope and prototype cross-check

Cross-check added 2026-11-02, Australia/Sydney, against `AUDIT_REPORT_prototype-e2e.md`. This is a follow-up comparison: the broader prototype file inventory remains in that report, subject to the corrections below; the original nine-section main baseline is retained for comparison.

**Correction to my original audit:** I inspected the checked-out `main` tree but missed the working implementation in this folder's local Git history. `prototype/e2e` points to `4b5ef3a5ef9e6f1ca69d54aaa2f9236ae087740b`, 23 commits ahead of `main` at `2d08ae1d41e4122bec8390475c692a887c6c5999`. That source was inside the permitted audit scope. My original finding that the full system was unavailable for assessment was incomplete. The phase 1 findings remain valid for `main`, but several are already fixed in the prototype and must not be presented as defects in the working system.

I exported the exact prototype commit from this folder's `.git` to `/tmp/happyrobot-crosscheck.R6tNd4/prototype`, without changing branches, and independently read the critical implementation paths. The export contains the API, Twin/FMCSA/email adapters, workflow artifacts, Apps source, Dockerfile and deployment scripts. No live service was contacted. Only this report was edited; the comparison report was left unchanged.

### Corrected verdict

- `service/core/`: **refactor**, retain algorithms/state meanings; extract the 704-line runtime's application use cases and finish explicit contracts.
- `service/adapters/`: **refactor**, preserve one-shot TMS/evidence behavior; fix reservation recovery, receipt completion and atomic audit/state handling.
- `service/api/` and `service/config.py`: **refactor**, extract existing routes/composition/collection and add validated settings; wholesale replacement is not yet justified.
- `service/tests/`, `happyrobot/`, `ops-app/` and deployment: **retain the working contracts, add production-path tests and improve reproducibility**; verify deployment/source parity separately.
- **Overall: targeted refactor, not a system rewrite.** Review and reconcile the prototype with `main` before publication; no merge or push was performed or authorized by this cross-check.

### Independently reconciled measurements

Tools ran from temporary directories on **Python 3.12.16**, using the prototype's three pinned direct dependencies. Resolved FastAPI 0.121.1, Starlette 0.49.3, Uvicorn 0.38.0 and HTTPX 0.28.1 match the other report. Ruff 0.17.3, mypy 2.4.1, radon 6.0.1 and Coverage.py 7.17.0 also match. Tests ran with a clean environment, bytecode disabled and an OS sandbox denying non-loopback outbound network, in addition to their Python network guard.

| Check | This cross-check | Other report | Result |
|---|---|---|---|
| Prototype tests | 187 passed, 6.798 seconds under coverage | 187 passed, 7.131 seconds | Reproduced; timing differs |
| Ruff, isolated defaults, `service/` | 98 findings, 64 marked fixable | 98, 64 fixable | Reproduced |
| Strict mypy, all `service/` | 1375 errors, 47 files, 55 checked | Same | Reproduced |
| Strict mypy, excluding `service/tests` | 587 errors, 32 files, 40 checked | Same | Reproduced |
| Radon, excluding tests | 219 blocks, mean 4.757990867579909; A159/B33/C23/D3/E1 | 219, mean 4.76; same ranks | Reproduced |
| Radon production raw | LOC4501, LLOC2945, SLOC3857, comments31, blank509 | LOC4501, SLOC3857, comments31, blank509 | Reproduced |
| Same-scope `main` control | 112 tests passed; strict mypy 150 errors in 10 files, 15 checked | 112 tests; 150 strict errors | Reproduced |

Commands used, with working directory `/tmp/happyrobot-crosscheck.R6tNd4/prototype`, except the `main` control which used the original temporary main snapshot:

```sh
../venv/bin/ruff check --isolated --no-cache --statistics service
../venv/bin/mypy --config-file /tmp/happyrobot-crosscheck.R6tNd4/mypy.ini --strict --cache-dir /tmp/happyrobot-crosscheck.R6tNd4/mypy-all-cache service
../venv/bin/mypy --config-file /tmp/happyrobot-crosscheck.R6tNd4/mypy.ini --strict --cache-dir /tmp/happyrobot-crosscheck.R6tNd4/mypy-production-cache --exclude service/tests service
../venv/bin/radon cc -s -a --exclude 'service/tests/*' service
../venv/bin/radon cc -j --exclude 'service/tests/*' service
../venv/bin/radon mi -s service
../venv/bin/radon raw -s --exclude 'service/tests/*' service
```

The temporary mypy config is empty apart from `[mypy]`. The coverage runner used this argument vector through `subprocess.run`, with only temporary-tool `PATH`, `PYTHONDONTWRITEBYTECODE=1` and `COVERAGE_FILE=/tmp/happyrobot-crosscheck.R6tNd4/prototype.coverage` in its environment:

```sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))(allow network-outbound (remote ip "localhost:*"))' /tmp/happyrobot-crosscheck.R6tNd4/venv/bin/coverage run --branch --source=service --omit='service/tests/*' -m unittest discover -s service/tests -t .
```

Coverage JSON was generated from each data file, using `coverage json --omit='service/tests/*' -o <temporary-output>`. Separate filtered results also omitted `service/scripts/*` and `service/adapters/tms/fake.py`.

| Matching Python 3.12 scope | Statements covered | Branch outcomes covered | Combined Cover |
|---|---:|---:|---:|
| Prototype, service excluding tests | 1734/2317, **74.84%** | 540/824, **65.53%** | **72.40%** |
| Main, service excluding tests | 705/724, **97.38%** | 203/218, **93.12%** | **96.39%** |
| Prototype runtime, also excluding service scripts/fake | 1562/2058, **75.90%** | 493/746, **66.09%** | **73.29%** |
| Main runtime, also excluding fake | 568/579, **98.10%** | 165/174, **94.83%** | **97.34%** |

The other report's 96-to-72 combined-coverage comparison is reproducible under matching settings. However, it calls the combined `Cover` percentage branch coverage, which is incorrect. For example, prototype `api/app.py` has **24/62 branch outcomes covered, 38.71%**, not 54%; 54% is its combined coverage. `core/calls.py` has **121/168, 72.02% branch coverage**, not 79%. Coverage targets must use the intended denominator.

My original 97.17% combined result below excluded fake/scripts and ran Python 3.14.0. It should not be directly compared with the prototype's broader 72% figure. Python/compiler differences also change statement counts. None of these percentages establishes correctness.

### Reconciliation of my earlier findings

All references in this subsection point to prototype commit `4b5ef3a`, not the checked-out `main` files.

| Original main finding | Actual prototype state |
|---|---|
| Missing HTTP/storage/workflow/dashboard source | Exists in local Git branch; this is source/publication provenance, not absent implementation |
| Cancellation can abandon submission | Owned task set plus `asyncio.shield` at `core/booking.py:179-182`; shutdown waits for booking tasks at `api/app.py:120-121` |
| No transport stage/partial evidence; false unknown before connection | Stage/bytes retained at `adapters/tms/client.py:229-269`; proven no-send is rejected; fsynced receipt journal is used |
| Rep decision race | Decision checked inside versioned `mutate`, `adapters/twin/bookings.py:181-200`; the main-only race is fixed in this path |
| Unknown called accepted and confirmable | Neutral `senior_review` at `core/booking.py:146-156`; confirmation guard at lines 344-351 |
| Past pickup accepted | Final pickup check at `core/booking.py:199-200` |
| Caller-supplied agreement/invalid offer might authorize booking | HTTP rejects rate/MC/load arguments at `api/app.py:267-272`; `Runtime.book` uses stored agreement; `Runtime.negotiate` clamps current offer to fresh cap at `core/calls.py:464-468` |
| Receipt lost immediately on first save error | Improved: three attempts, readback and fallback log at `core/booking.py:234-274`, plus journal-based startup recovery; exhaustion and durability gaps remain |
| State/audit disagreement | Confirmed in actual code, not merely the old architecture proposal: state CAS precedes best-effort `defer_aux` |
| Implicit types/config/policy loader | Still present; prototype strict typing has 587 production-scope errors and `PricingPolicy.load` still reads a file |

The pure `respond` precondition and invalid-policy probes below remain valid library-level observations. They do not demonstrate an HTTP excessive-price bypass in the prototype, whose caller applies additional constraints.

### Independently reproduced prototype failures

I rebuilt focused probes instead of treating the other audit's scenarios as verified facts. They exercise actual `Runtime`, `BookingService`, `TwinBookingStore` and production deferred-save behavior over memory/scripted dependencies. All socket connection entry points are blocked. These prove application ordering failures, not actual Twin SQL behavior.

```text
freeze_rejection: active_claims=2 booking_rows=0 blocked=true sends=0
post_intent_deadline: state=FAILED retained_intent=true send_started=false blocked=true sends=0
audit_save_failure: rounds=1 events=0 projection_errors=1
repeat_close: first_closed_at=100 second_closed_at=106
receipt_retry_exhaustion: attempts=3 returned=ACK_PENDING persistence_pending=true stored=SUBMITTING reference=None fallback_logs=1 sends=1
otp_promotion_failure: consumed_at=100 verified_until=0 retry_status=code_expired_or_used
probes=6 passed=6 socket_connections=0
```

Command, from `/tmp/happyrobot-crosscheck.R6tNd4`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/happyrobot-crosscheck.R6tNd4/prototype python3 /tmp/happyrobot-crosscheck.R6tNd4/prototype_probes.py
```

The first five corroborate the other audit's central concerns: claims can outlive a failed reservation; a proven no-send can stay blocked; audit writes can vanish after committed state; close is not idempotent beyond the retry window; and exhausted receipt persistence can return acknowledged state while stored state remains submitting.

**Additional finding not captured by the other report's assurance that critical rows hold up:** `core/calls.py:299-311` commits OTP consumption, then lines 314-333 separately promote call verification. Failing the second call update leaves a consumed correct code and an unverified call; retry returns `code_expired_or_used`. Individual CAS operations prevent double consumption but do not make this two-row transition atomic. This fails closed, so it is an availability/recovery defect, not a demonstrated verification bypass. Co-locate active challenge and verification in one call-row transition, or implement explicit idempotent recovery tied to challenge and call revision. Adding row history alone does not fix it.

### Corrections required in the prototype report

1. **Orphan cleanup is not proved safe from an absent booking row.** Its line 312 asserts that a claim without a booking can safely be released. A creator can be paused after acquiring claims and before inserting its booking (`adapters/twin/bookings.py:82-138`), or an insert response can be lost after commit. Fence the creator/attempt first, for example with a terminal tombstone under the same booking identity before releasing owned claims, or establish the prior worker cannot resume. Catch-and-release also needs an explicit failed no-send attempt because `release` refuses non-FAILED bookings at lines 142-144. Cleanup failures must be retained for retry. A process-local close lock is useful but does not prove cross-process recovery safe.

2. **Retain intent evidence when fixing no-send inventory blocks.** The proposed one-line `write_intent_id=None` can make existing predicates release when the same winning coroutine knows no send began. It is not by itself proof of duplicate sending. But it destroys the durable intent/journal identity to encode liveness. Prefer an immutable intent plus explicit terminal proof of no-send, and update release, active uniqueness, `for_call` and blocked-load predicates consistently. Never release based merely on a missing receipt or stale OPEN status.

3. **Correct receipt-retry wording and durability claims.** Production `_record` already tries three times. Its sleeps total 0.15 seconds, but SQL/readback execution adds to elapsed time. The remaining gap is no continuing retry after exhaustion and no guaranteed remotely durable receipt recovery. The local journal is fsynced and startup recovery uses it; no mount establishes a machine-replacement limitation, not proof that ordinary auto-stop erases its contents. An in-process retry list improves recovery while alive but cannot solve process loss by itself.

4. **Injected settings lookups are not environment reads.** `core/calls.py:34,46,205,341` read an injected `values` mapping. Actual environment I/O is at `config.py:17`. The precise issue is an overbroad, untyped configuration dependency and hidden policy construction. Conversely, its claim that all of `pricing.py` is pure is wrong: lines 29-38 load JSON, and `Runtime` invokes that loader at `core/calls.py:37`. Preserve price arithmetic, extract and validate loading.

5. **Prefer incremental refactoring of API/config.** The evidence supports separating the 335-line app factory's routing, auth, composition and transcript collection, and replacing the 18-line settings parser with validated settings. It does not demonstrate that existing behavior must be discarded. The other report's own later plan largely describes extraction. A small settings replacement may be practical, but it is not evidence for a broader rewrite.

6. **Keep the storage recommendation conditional and complete.** Same-row history plus derived booking outcomes is a sound direction under the supplied constraints. Multi-row flush support, row growth limits and safe pruning remain unverified. Use stable event IDs and acknowledged sequence watermarks; retained history length cannot be compared with lifetime event count after trimming. Include flush acknowledgment/pruning writes in capacity estimates, and fix OTP consumption/promotion separately. The proposed multi-table CTE is unavailable under the current no-multi-table-transaction constraint, not a capability to assume. A compliant external coordinator still mirrors activity to Twin, so its Twin cost is not zero.

7. **Bound operational/provenance claims.** Local refs confirm 23 commits ahead, no configured upstream and no locally known remote-tracking branch containing this commit. They do not prove no remote copy or backup exists. The Mac Docker-plugin path is guarded by `vendor.exists()` at `service/scripts/deploy.py:24`, so it does not establish a mandatory Mac dependency; fixed application settings and the private interpreter path are real reproducibility concerns. Historical code/hash evidence is not a fresh live verification. Runtime Python code parity is narrower than parity of every policy/artifact used during the successful call.

8. **Coverage and safety claims need precise limits.** The coverage denominator correction is above. Tests that relabel `MemoryRepository` after constructing `Runtime` leave `booking_store.live=False`, so they miss the actual live freeze/intent guards despite exercising Runtime consent (`test_runtime.py:54,444,476`; `core/calls.py:39-41`). A marked-ceiling response scan and one booking call site do not prove universal secrecy or at-most-once behavior under every failure schedule. The other report's capacity simulations, dependency-advisory counts, image build and dashboard checks were not independently rerun here; treat them as attributed evidence, with stated model assumptions and unresolved exploitability.

### Corrected HTTP-to-storage reading

The previously unavailable path is now inspectable: workflow-mapped trusted `run_id` reaches `POST /bookings`; middleware authenticates and applies a deadline (`api/app.py:125-163`); the route rejects authoritative booking fields and enters the per-call lock; `Runtime.book` reads stored call/agreement and native consent; `TwinBookingStore.create` claims call/load, freezes the call, and inserts the booking; `BookingService` rechecks eligibility and persists intent, sends once, saves evidence, and updates call outcome. `TwinRepository` implements actual SQL at `adapters/twin/repository.py:191-293`.

The important failure boundaries are claim-to-freeze-to-booking insertion, call-to-challenge verification, state-to-deferred audit, and receipt-to-stored state. Source inspection confirms these boundaries. This cross-check did not execute Twin SQL, re-create the other report's exact 21-statement pacing model, or observe the live call. The current suite's lack of successful HTTP coverage for booking/close/rep and lifespan remains a material gap.

### Priorities after cross-check

Preserve the working protocol, consent behavior and HTTP contracts. First add production-path regressions for the six failures above. Then fix fenced reservation cleanup, explicit proven-no-send release, recoverable receipt persistence, atomic state/audit history and OTP consumption/promotion. Add supervised audit draining and visible error/lag counters, without describing draining alone as crash durability. Extract runtime/API/config responsibilities incrementally after these tests exist. Keep the source-provenance and owner-review gate before integrating or pushing the branch.

The original nine-section report below is retained as a **main-only historical baseline**, including its original measurements and file table. Its missing-implementation and fixed-booking findings are superseded for the prototype by this addendum. The other report is the broader prototype inventory, subject to the corrections and verification limits above.


# Original audit: main-only historical baseline

Audit date: 2026-11-02, Australia/Sydney. Audited checkout: `main`, commit `2d08ae1d41e4122bec8390475c692a887c6c5999`. Initial Git status was clean.

Scope: the supplied folder only. The assignment PDF was read locally. The first read-only `pwd`/`rg` inventory used the repository working directory, contrary to the requested tool-location constraint; all later shell commands and executable checks used temporary directories. Measurements used a copied snapshot in `/tmp/happyrobot-audit.lynVua`, with a temporary virtual environment, caches and outputs. Initial read-only inspections/probes also read original in-scope files with bytecode disabled. Network access was used only to install audit packages after the owner's explicit permission. No project service, workflow, email provider, TMS or Twin was contacted. No booking inventory was spent. No commit or push was made.

**Material discrepancy:** this folder contains a phase 1 Python library, not the working HTTP backend, workflow and dashboard described in the request. `service/README.md:3` explicitly says there are no endpoints; line 46 lists Twin, authentication, FMCSA, email, Docker and deployment as unbuilt. A filename inventory, including ignored directories, found historical TMS studies and a lab, but no missing production API or dashboard. The newer owner-reported live constraints and successful call are accepted as context; old documentation is not used to contradict them. Their implementation cannot be audited from this snapshot.

## 1. Verdict

- `service/core/`: **refactor**, retain pricing, money, load and booking rules; repair invariants and separate application orchestration from domain data.
- `service/adapters/`: **refactor**, retain protocol and mapping; repair transport evidence and cancellation handling; move the fake into tests.
- `service/tests/` and `scripts/`: **keep tests, refactor helpers and CLI**, preserve fault cases and remove duplicate protocol ownership.
- `docs/` and root guides: **keep evidence, refactor status and delivery material**, tie every implementation claim to the submitted commit.
- `happyrobot/`, `ops-app/` and deployment: **unassessable because absent**; obtain the exact tested artifacts before deciding to keep, refactor or rewrite them. No whole-system rewrite is justified.

## 2. Measurements

### Reproduction and tool versions

The snapshot contains unchanged copies of `service/`, `scripts/`, `docs/`, the assignment PDF and selected root guides/configuration examples. SHA-256 digests were recorded for 38 copied source/reference files. Credentials and historical write harnesses were neither copied nor executed. All Python executions disabled source bytecode writes where applicable. The service tests use loopback TCP; the extra storage probes block all socket connections.

Actual runtime: Python **3.14.0**, not the documented deployment target 3.12. Type checking explicitly targeted 3.12. Tools: Ruff **0.17.3**, mypy **2.4.1**, radon **6.0.1**, Coverage.py **7.17.0**. These versions were installed in the temporary virtual environment. The production code uses the standard library; installing audit tools did not add project dependencies.

Commands below ran with working directory `/tmp/happyrobot-audit.lynVua/snapshot`. `../venv/bin/` is the temporary environment. The explicit temporary mypy configuration contains only `[mypy]`; Ruff used `--isolated` to disable configuration discovery. No autofix command was run.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s service/tests -t .
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_query_loads.py
../venv/bin/ruff check --isolated --no-cache service scripts
../venv/bin/ruff check --isolated --no-cache --statistics service scripts
../venv/bin/ruff check --isolated --no-cache --select E,F,I,UP,B,SIM --target-version py312 --statistics service scripts
../venv/bin/mypy --config-file /tmp/happyrobot-audit.lynVua/mypy.ini --strict --python-version 3.12 --cache-dir /tmp/happyrobot-audit.lynVua/mypy-all-isolated-cache service scripts
../venv/bin/mypy --config-file /tmp/happyrobot-audit.lynVua/mypy.ini --strict --python-version 3.12 --cache-dir /tmp/happyrobot-audit.lynVua/mypy-production-isolated-cache --exclude '(service/tests/|service/adapters/tms/fake.py)' service
../venv/bin/radon cc -s -a service scripts
../venv/bin/radon cc -j service scripts
../venv/bin/radon raw -s service scripts
../venv/bin/radon mi -s service scripts
PYTHONDONTWRITEBYTECODE=1 COVERAGE_FILE=/tmp/happyrobot-audit.lynVua/.coverage ../venv/bin/coverage run --branch --source=service --omit='service/tests/*,service/adapters/tms/fake.py' -m unittest discover -s service/tests -t .
COVERAGE_FILE=/tmp/happyrobot-audit.lynVua/.coverage ../venv/bin/coverage report --rcfile=/tmp/happyrobot-audit.lynVua/coverage.ini
COVERAGE_FILE=/tmp/happyrobot-audit.lynVua/.coverage ../venv/bin/coverage json --rcfile=/tmp/happyrobot-audit.lynVua/coverage.ini -o /tmp/happyrobot-audit.lynVua/coverage.json
```

The temporary coverage report configuration sets `branch=True`, `source=service`, omits `service/tests/*` and `service/adapters/tms/fake.py`, shows missing lines and uses two decimal places. It does not add manual exclusion rules. The raw coverage data came from the command above.

| Measurement | Raw result | Exit |
|---|---|---:|
| Service unittest run | 112 tests, 5.067 seconds, OK | 0 |
| Reader unittest run | 7 tests, 1.005 seconds, OK | 0 |
| Service unittest run under coverage | 112 tests, 5.281 seconds, OK | 0 |
| Ruff isolated default rules | 19 findings, 16 marked automatically fixable | 1 |
| Ruff explicit expanded rule set | 95 findings | 1 |
| mypy strict, service plus scripts including tests/fake | 580 errors in 18 files, 23 source files checked | 1 |
| mypy strict, production service excluding tests/fake | 124 errors in 9 files, 14 source files checked | 1 |
| radon CC, service plus scripts | 262 blocks, mean 2.366412213740458, rank A | 0 |
| Coverage, production service excluding tests/fake | 533 statements, 11 missed; 174 branch outcomes, 9 missed, 9 partial branches | 0 |

Ruff default breakdown: `I001=10`, `F401=3`, `UP017=2`, `ISC004=1`, `FURB167=1`, `PLW1510=1`, `C408=1`. Expanded breakdown: `E501=80`, `I001=10`, `F401=3`, `UP017=2`. Different rule selections produce different totals. These are mostly style findings and are not the basis of the correctness verdict.

Mypy production breakdown: `no-untyped-def=54`, `no-untyped-call=60`, `type-arg=10`. Full-tree breakdown: `no-untyped-def=216`, `no-untyped-call=346`, `type-arg=11`, `var-annotated=2`, `union-attr=2`, `assignment=1`, `method-assign=2`. Most diagnostics concern missing contracts rather than 580 independent runtime bugs. A separate AST count found only 7 of 60 production function/method definitions had complete parameter and return annotations, excluding `self`/`cls` and excluding the fake.

Radon raw totals for `service/` plus `scripts/`: **LOC 2538, LLOC 1856, SLOC 2001, comments 20, single comments 58, multiline-string lines 39, blank lines 440**. Those are radon's categories, not interchangeable definitions of code size. `service/` contains 23 files: 21 Python files plus README and policy JSON. Its Python files total 2285 physical lines, comprising 938 production lines, 214 fake lines and 1133 test/helper lines.

Radon CC distribution, all 262 blocks: **A=243, B=12, C=7**. Production service alone, excluding tests/fake: **84 blocks, mean 3.1785714285714284, A=72, B=7, C=5**. Radon counts classes as well as functions/methods; averages are not a timing or comprehension measurement.

| Highest-complexity block | CC | Rank |
|---|---:|---|
| `service/adapters/tms/protocol.py:86`, `parse_reply` | 18 | C |
| `scripts/query_loads.py:89`, `main` | 16 | C |
| `service/adapters/tms/client.py:131`, `query` | 15 | C |
| `service/adapters/tms/fake.py:111`, `_respond` | 15 | C |
| `service/core/booking.py:258`, `reconcile` | 13 | C |
| `service/adapters/tms/protocol.py:42`, `encode_request` | 12 | C |
| `service/core/pricing.py:61`, `price_load` | 11 | C |

Radon MI scores, all graded A by radon's thresholds: `client.py=24.51`, `protocol.py=45.30`, `mapping.py=52.08`, `fake.py=40.30`, `booking.py=33.95`, `loads.py=57.83`, `models.py=59.21`, `money.py=62.61`, `negotiation.py=52.31`, `ports.py=58.11`, `pricing.py=57.43`, `tests/support.py=61.29`, `test_booking.py=20.52`, `test_client.py=32.62`, `test_pricing.py=33.20`, `test_protocol.py=31.44`, `scripts/query_loads.py=52.45`, `scripts/test_query_loads.py=59.53`. Empty package markers and the three-line test package initializer score 100. An A grade is not evidence that the enterprise standard is met.

Coverage raw per-module output, with punctuation normalized to ASCII:

```text
Name                               Stmts   Miss Branch BrPart   Cover   Missing
service/__init__.py                    0      0      0      0 100.00%
service/adapters/__init__.py           0      0      0      0 100.00%
service/adapters/tms/__init__.py       0      0      0      0 100.00%
service/adapters/tms/client.py       144      6     58      4  95.05%   128,153,162,165-166,176
service/adapters/tms/mapping.py       35      1      6      1  95.12%   41
service/adapters/tms/protocol.py      81      0     44      0 100.00%
service/core/__init__.py               0      0      0      0 100.00%
service/core/booking.py              154      3     44      3  96.97%   139,188,262
service/core/loads.py                  9      0      0      0 100.00%
service/core/models.py                14      0      0      0 100.00%
service/core/money.py                 11      0      4      0 100.00%
service/core/negotiation.py           26      0      8      0 100.00%
service/core/ports.py                 17      0      0      0 100.00%
service/core/pricing.py               42      1     10      1  96.15%   87
TOTAL                                533     11    174      9  97.17%
```

Coverage JSON separates the denominators: **522/533 statements covered, 97.94%; 165/174 branch outcomes covered, 94.83%; combined 97.17%**. Thirteen protocol-declaration lines were excluded by coverage defaults. The fake, tests, reader CLI, absent adapters and absent HTTP/dashboard code are outside this coverage result. This measures execution, not correctness: existing assertions explicitly require false-unknown and unsupported-acceptance behavior.

### Additional offline reproductions

These audit-only scripts exist in the temporary directory, not in the repository. Commands ran from `/tmp/happyrobot-audit.lynVua`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/happyrobot-audit.lynVua/snapshot python3 /tmp/happyrobot-audit.lynVua/storage_probes.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/happyrobot-audit.lynVua/snapshot /tmp/happyrobot-audit.lynVua/venv/bin/python /tmp/happyrobot-audit.lynVua/trace_and_policy_probes.py
```

Observed output:

```text
unknown_confirm: state=UNKNOWN rep_decision=confirmed agent_status=request_accepted
concurrent_rep_decisions: both_succeeded=true final_decision=declined
past_pickup: pickup=20000101000000 state=ACK_PENDING sends=1
receipt_save_failure: state=SUBMITTING reference=None raw_reply=None sends=1
request_cancellation: state=SUBMITTING sends=1
successful_core_trace: STORE.CREATE:AGREED -> TMS.GET -> STORE.UPDATE:SUBMITTING -> TMS.BOOK -> STORE.UPDATE:ACK_PENDING
probes=6 passed=6 socket_connections=0
invalid_current_offer: accept 4000 cap=2300
negative_round: counter 2300 rounds=0
zero_rounding: ZeroDivisionError
empty_targets: IndexError
```

Here, six passed probes means the six described observations were reproduced, including the defects. It is not a claim of six successful production acceptance tests. The representative race uses a store that snapshots a read and yields before returning, reproducing a possible SQL I/O interleaving. The cancellation and receipt-save probes use scripted TMS objects and no sockets.

### Request-to-storage trace

**A full HTTP-call trace cannot be completed:** there is no HTTP entry point, request model, authentication middleware, trusted-run-ID binding, verification/OTP application, Twin adapter or call-state writer in this folder. The first and last mandatory boundaries are missing. The planned `POST /bookings` at `ARCHITECTURE.md:214` is documentation, not executable code.

The complete implemented booking path was read and exercised over real loopback TCP against the fake:

1. A direct Python call enters `BookingService.request` at `service/core/booking.py:149`. Inputs include caller-supplied `operation_id`, MC, rate and agreement version. Only positive-integer rate validation occurs here; there is no persisted identity/negotiation lookup.
2. Lines 153-157 hash inputs, construct `Booking`, and call `store.create`. `InMemoryBookingStore.create` at line 97 checks duplicate operations and active load/call conflicts, then changes two dictionaries. State becomes `AGREED`. This is process memory, not durable storage.
3. `_submit` at line 168 calls `TmsClient.get` at `client.py:168`. `_read` encodes `LOAD_GET`, `_exchange` at line 82 opens one TCP connection, and the protocol parser plus mapping return `Load`.
4. `booking.py:175-180` checks `OPEN`, ceiling availability and rate. Lines 183-186 conditionally replace the in-memory booking with `SUBMITTING` and a write intent.
5. `client.py:179-196` validates MC/rate, encodes one `LOAD_BOOK` request and opens another connection. There is no write retry. The fake returns a reference-bearing `PENDING` response.
6. `classify_booking_reply` at `client.py:41` maps that reply to `ACK_PENDING`; `_record` at `booking.py:192` replaces the stored booking with state, reference, status and raw reply.
7. `agent_view` at line 130 returns the permitted response fields. No call audit record or Twin SQL statement is written anywhere in this trace.

Observed final state: `ACK_PENDING`, synthetic reference `FAKE000000000001`, exactly one fake booking send, and equality between returned and in-memory stored booking. This proves that library path under those inputs. It cannot establish the missing HTTP-to-Twin path or the owner's real end-to-end call.

## 3. Top 10 problems, most serious first

1. **Submission source does not contain the claimed tested system.** `service/README.md:3`, `service/README.md:46`, `docs/agent-onboarding.md:20`, `docs/platform-checks.md:42`. There is no executable implementation of the assignment's authenticated call flow, Twin audit, Apps dashboard or Docker deployment here. The documented 98-test harness is explicitly a different codebase. A reviewer cannot reproduce or defend the submitted system. **Smallest fix:** bring the exact tested backend, sanitized workflow/version, dashboard source and deployment artifacts into the submission with commit provenance, then audit that version. Do not rebuild the missing system merely to fill this checkout. This is a blocker in the supplied snapshot, not proof that the owner's deployed system lacks those features.

2. **Irreplaceable booking receipts disappear when persistence fails.** `service/core/booking.py:189`, `service/core/booking.py:192`. A successful external reply is immediately handed to an unprotected store update. If the update raises, there is no retry or recoverable receipt sink. The probe retained `SUBMITTING`, no reference and no raw reply after one accepted synthetic send. TMS readback cannot reconstruct ownership or receipt. **Smallest fix:** retain an immutable, sanitized receipt in a supervised completion task; retry only its storage with bounded backoff; on exhaustion, write recoverable evidence to an explicitly configured durable sink and alert. Preserve uncertainty and never retry `LOAD_BOOK`.

3. **Request cancellation interrupts the irreversible send/save path.** `service/core/booking.py:183`, `service/core/booking.py:189`. A caller timeout or disconnect can cancel `tms.book` after the external side effect begins, leaving no receipt and a stuck `SUBMITTING` record. The probe reproduced this. **Smallest fix:** give send plus receipt persistence to a supervisor-owned task, started only after durable write intent. Request cancellation stops waiting, not completion. Drain tracked tasks on shutdown; recover truly interrupted sends as unknown. A bare `asyncio.shield` without task ownership and shutdown handling is incomplete.

4. **Transport failures erase evidence and cannot distinguish no-send from maybe-sent.** `service/adapters/tms/client.py:82`, `service/adapters/tms/client.py:194`. Received bytes live only in `_exchange`'s local buffer. On timeout/reset/bounds failure the receipt keeps only the exception name. Connection refusal is also `UNKNOWN`, unnecessarily blocking a load even though no connection opened; `service/tests/test_client.py:215` requires this wrong behavior. **Smallest fix:** return a typed transport result/error containing connect/write/read stage, send-start flag and sanitized received bytes/count/hash. A proven failure before any possible write is `FAILED`; anything potentially sent stays `UNKNOWN`. Never infer no-send from a failed `drain`.

5. **Representative decisions can reverse under concurrency.** `service/core/booking.py:229`, `service/core/booking.py:235`, `service/core/booking.py:80`. The code checks the prior representative decision, then conditions its write only on booking state. Confirm and decline do not change that state, so both can succeed after overlapping reads. The yielding-store probe returned both successes and ended declined. This is a defect in the storage contract when I/O yields; the current non-yielding memory store serializes these methods and conceals it. **Smallest fix:** condition the write on expected revision and expected representative decision. Return a conflict for the loser. Extend the port to express this, and test interleaving at real await boundaries. A process-local lock alone does not cover deployment overlap.

6. **Unknown outcomes are represented as accepted and may be confirmed.** `service/core/booking.py:34`, `service/core/booking.py:140`, `service/core/booking.py:240`. `UNKNOWN` returns `request_accepted`, despite a lost/unprocessed request being possible, and `confirm` accepts it. `service/tests/test_booking.py:410` codifies the acceptance claim. This contradicts the documented rule at `ARCHITECTURE.md:217` and line 339. **Smallest fix:** use a neutral carrier status that claims no receipt; allow representative confirmation only for `ACK_PENDING` or authoritative `CONFIRMED`. Keep unknown review/decline available. A representative confirmation remains a local fact, never TMS finality.

7. **Negotiation and agreement ownership are not enforced at the application boundary.** `service/core/negotiation.py:26`, `service/core/negotiation.py:31`, `service/core/booking.py:149`. Negotiation trusts supplied current offer and round count. With cap 2300, offer 5000 and ask 4000 it accepts 4000; a negative round indexes the final target. Booking accepts supplied MC/rate/version without loading an authorized agreement. The final check rejects rates above the current TMS ceiling, but does not enforce the policy cap or persisted agreement. It does not prevent an excessive spoken offer or an unauthorized below-ceiling booking. There is no HTTP caller here to prove exposure or mitigation. **Smallest fix:** validate function preconditions and make one application use case load verified call state and immutable agreement from storage. The model supplies intent, never authoritative budgets, offer, identity or agreed price. Derive booking retry keys server-side from trusted run ID, load and agreement version; the platform supplies no stable operation ID.

8. **The last booking check allows past or invalid pickups.** `service/core/booking.py:175`, compared with `service/core/loads.py:6`. Selection checks future pickup, but booking rechecks only status and ceiling. An `OPEN` record dated 2000 produced a synthetic send and `ACK_PENDING`. **Smallest fix:** inject a clock, check valid future pickup immediately before intent/send, and reuse the eligibility predicate without rejecting the booking's own already-claimed load. This preserves successful future-pickup cases and closes stale-selection cases.

9. **The proposed normalized Twin model has no atomic state/audit contract.** `ARCHITECTURE.md:350`, `ARCHITECTURE.md:352`, `ARCHITECTURE.md:358`, `ARCHITECTURE.md:368`. Calls, events, challenges, rounds and bookings are separate mutable records. Under the verified single-statement/no-multi-table-transaction interface, a state update and audit insert can disagree. Unique claims and row versions do not make those writes atomic. The only implemented store at `service/core/booking.py:90` is in-memory, so the actual deployed remedy is unavailable for review. **Smallest fix:** define each authoritative state transition and its audit/outbox append as one conditional update to one record, then project reporting records idempotently. Keep booking truth in its booking record and expose projection lag. Details and alternatives follow in sections 5 and 6.

10. **Core contracts are implicit, and policy loading mixes I/O with business rules.** `service/core/booking.py:73`, `service/core/booking.py:80`, `service/core/pricing.py:16`, `service/core/pricing.py:29`, `service/core/pricing.py:85`. Generic tuples/lists, untyped dependencies and `**changes` obscure allowed transitions; strict mypy finds 124 production errors. Pricing reads JSON from an implicit module-relative path and accepts invalid shapes: zero rounding crashes, empty targets crash, too few targets can fail later in negotiation. **Smallest fix:** add concrete input/result types and explicit versioned store methods; load and validate settings/policy once in composition. Inject the resulting immutable values and clock/ID sources. Avoid building a generic repository or workflow framework.

Additional issues below the top ten: importing `service.tests` permanently replaces global socket methods (`service/tests/support.py:23`), so test isolation depends on import order; scope and restore the guard. `scripts/query_loads.py:54-86` duplicates transport/framing logic with weaker validation; characterize its output then reuse the service adapter. UTC is an explicit but unverified TMS timestamp assumption (`mapping.py:14`); do not describe it as confirmed. Hiding a ceiling from `repr` does not prevent serialization or deliberate inference; the absent API's allowlist and adversarial results remain unverified.

## 4. File table for service/

Sizes are physical lines, including comments and blanks. Targets describe approximate destination-module sizes after extraction; they are guidance, not incentives to compress code. Test-file targets can exceed runtime-module targets because cases are independently readable. No current file needs wholesale deletion or rewrite. Moving the fake/store removes them from production paths without discarding their tests.

| Current file | Current lines | Verdict | One-line reason and approximate target |
|---|---:|---|---|
| `service/README.md` | 46 | refactor | Replace phase-only instructions with exact entry point, configuration and supported scope; 80-120 lines. |
| `service/__init__.py` | 0 | keep | Empty package marker, no import-time composition; 0 lines. |
| `service/adapters/__init__.py` | 0 | keep | Empty package marker; 0 lines. |
| `service/adapters/tms/__init__.py` | 0 | keep | Empty package marker, avoid a re-export layer; 0 lines. |
| `service/adapters/tms/client.py` | 196 | refactor | Preserve one-request connections and no write retry, add typed transport evidence; 150-220 lines plus 70-110 transport lines if extracted. |
| `service/adapters/tms/protocol.py` | 120 | keep | Pure parser/encoder has full measured statement/branch coverage and explicit bounds; 120-150 lines after typing. |
| `service/adapters/tms/mapping.py` | 78 | keep | Explicit mapping owns unit conversion and timestamp assumption; 80-110 lines after typing/validation. |
| `service/adapters/tms/fake.py` | 214 | refactor | Move unchanged behavior under `tests/fakes/tms.py`, then type it; 220-280 lines. |
| `service/core/__init__.py` | 0 | keep | Empty package marker; 0 lines. |
| `service/core/booking.py` | 284 | refactor | Currently owns entity, port, memory store, presentation and orchestration; 90-130 domain lines, move request/recovery to application modules and fake store to tests. |
| `service/core/loads.py` | 28 | keep | Small pure selection policy, add explicit types and reuse eligibility before booking; 35-55 lines. |
| `service/core/models.py` | 48 | keep | Explicit immutable data records, retain secret-field handling without claiming serialization safety; 55-85 lines. |
| `service/core/money.py` | 20 | keep | Exact whole-value parsing has direct tests and no float-based rounding; 25-35 lines. |
| `service/core/negotiation.py` | 41 | refactor | Keep deterministic calculation, validate offer/cap/round invariants; 55-85 lines. |
| `service/core/ports.py` | 35 | refactor | Move I/O contracts to application boundary and complete concrete results/revisions; 70-110 lines. |
| `service/core/pricing.py` | 88 | refactor | Keep arithmetic/HMAC calculation, move filesystem loading to configuration; 70-100 pure-domain lines. |
| `service/policy/pricing-v1.json` | 8 | keep | Explicit versioned policy, add startup validation rather than new configuration machinery; 8-15 lines. |
| `service/tests/__init__.py` | 3 | refactor | Remove permanent global mutation on import, enable scoped network fixture; 0-3 lines. |
| `service/tests/support.py` | 34 | refactor | Type helpers and restore socket methods reliably; 45-75 lines excluding extracted fake store. |
| `service/tests/test_booking.py` | 499 | refactor | Preserve characterized cases, split submission/recovery/rep/selection by behavior and add failure interleavings; roughly 150-250 lines per resulting file. |
| `service/tests/test_client.py` | 236 | refactor | Keep loopback fault tests, replace false-unknown assertion and add send-stage evidence/cancellation cases; roughly 180-260 lines per file. |
| `service/tests/test_pricing.py` | 148 | keep | Retain seeded randomized invariants, add invalid policy/offer/round cases; 180-240 lines. |
| `service/tests/test_protocol.py` | 213 | keep | Retain strict framing and six sanitized historical-reply fixtures; 220-280 lines after typing. |

Evidence for retention is narrow and specific: `core` imports no framework/third-party SDK; protocol parsing has no network; mapping is separate; booking distinguishes pending from authoritative confirmation; writes are not automatically retried; the randomized pricing test exercises 20,000 seeded loads. These facts justify preserving existing behavior where correct. They do not prove production security, confidentiality or durability.

## 5. Proposed design

This is a destination for incremental changes after obtaining the actual working source. It is not a request to implement every absent file again. Use an existing equivalent module if the working system already has one. Stay with one modular Python service and the native HappyRobot workflow/Apps UI.

```text
service/
|-- bootstrap.py                 # Build explicit dependencies and task supervisor
|-- config.py                    # Read/validate environment and policy once
|-- api/
|   |-- routes.py                # Authenticated HTTP mapping, no business decisions
|   `-- schemas.py               # Requests and allowlisted voice/ops responses
|-- application/
|   |-- calls.py                 # Trusted call lifecycle and retry-window handling
|   |-- verification.py          # Authority/code use cases and durable budgets
|   |-- sales.py                 # Search/negotiation over stored call state
|   |-- booking.py               # Agreement lookup, claim, send, recoverable save
|   |-- operations.py            # Rep decision and read-only reconciliation
|   `-- ports.py                 # Typed TMS/store/notifier/clock contracts
|-- core/
|   |-- models.py
|   |-- booking.py               # Data and legal state transitions
|   |-- loads.py
|   |-- money.py
|   |-- negotiation.py
|   `-- pricing.py               # Pure functions over validated policy
|-- adapters/
|   |-- tms/
|   |   |-- client.py
|   |   |-- transport.py         # Only if needed for explicit send evidence
|   |   |-- protocol.py
|   |   `-- mapping.py
|   |-- twin.py                  # Single-statement CAS/claim SQL only
|   |-- fmcsa.py                 # HTTP/schema mapping only
|   `-- email.py                 # Delivery only, no code policy
|-- policy/pricing-v1.json
`-- tests/
    |-- fakes/                   # Fake TCP TMS and memory stores
    |-- unit/
    `-- integration/             # Offline transport, races and fault recovery
happyrobot/                      # Sanitized export, prompt, tests, version provenance
ops-app/                         # HappyRobot Apps source, service-backed reads
schema/                          # Reviewed DDL applied via supported setup channel
Dockerfile
Makefile                         # One documented deployment command
```

```text
Carrier -> HappyRobot web call
                 |
          trusted run ID + workflow credential
                 v
       HTTP validation/authentication <--- Apps server + ops identity
                 |                              ^
                 v                              | read models/actions
       Application use cases ------------------+
            |           |
            v           v
       Pure core     Typed ports
                         |
             +-----------+------------+-------------+
             v           v            v             v
          TMS TCP    Twin SQL API   FMCSA HTTP    Email provider
             |           |
       one send only     +--> call state + same-row audit outbox
                         +--> booking claim/state/receipt + same-row outbox
                         `--> idempotent reporting projections
```

Runtime business functions receive configuration, policy, time and dependencies explicitly. Environment/file reads occur only during composition. Use ordinary dataclasses and small protocols, not a dependency-injection framework, generic state-machine engine or layers of repositories. HTTP models should not become domain models. Agent responses use explicit field allowlists; domain `Load` is never automatically serialized to the model.

### Storage consistency and throughput

The implemented store is two dictionaries in `booking.py:94-95`. Its operations do not yield internally, so concurrent tasks on one event loop appear serialized. The existing recovery test recreates `BookingService` over the **same store object** (`service/tests/test_booking.py:252`); it does not restart a process or prove durability. A process restart loses bookings, operations and blocked inventory. No actual Twin schema, SQL adapter or audit implementation is present.

The eight-table proposal is not implementable with the implied atomicity merely by adding version columns. Consider a counter: `UPDATE calls` consumes the round, then `INSERT negotiation_rounds` fails. The call budget changed but its audit did not. Reverse the order and an audit counter can exist without the budget changing. OTP consumption plus call verification and booking receipt plus copied call outcome have similar failure windows. Both records existing does not prove they agree on version or rate.

A naive event-start, budget-update, round-insert, event-finish sequence takes four statements. At the supplied roughly four statements/second ceiling, that is about one second of the entire shared statement budget for one counter, before reads, retries, concurrent calls or dashboard polling. This is capacity arithmetic, not a newly measured latency or SLA.

Recommended boundary: **one authoritative call aggregate and one authoritative booking aggregate**, with an audit-event/outbox payload updated in the same record and same conditional SQL statement as its state. Keep the active OTP hash, expiry, consumption, failed-attempt/send budgets, verified-until and call revision in that same call aggregate, so code consumption and verification are one conditional transition. Project challenge history separately. Keep carrier directory and large/redacted transcripts separate. Project query-friendly event/round/demand tables asynchronously, with deterministic event IDs and acknowledgment watermarks. Confirm that the supported Twin SQL and row-size limits can implement this before adopting it; primary-key winner tests alone do not establish JSON append/CAS, secondary constraints or response semantics.

Use this explicit booking sequence, with no cross-table transaction assumption:

1. CAS the call into an immutable prepared agreement containing trusted run ID, MC, load, rate, policy/agreement revision and server-owned intent ID. Save its event in that same call record. Freeze that agreement during submission; a later MC change cannot silently redirect it. A prepared agreement is not an external booking.
2. Insert the booking attempt keyed by the deterministic server-owned intent ID, with unique active-load and active-call fields in the **same booking table**, plus the immutable agreement snapshot. Schema/constraints are provisioned through a supported setup channel, not table creation over the SQL API. Conflicts return the existing attempt or a real conflict after input comparison.
3. Recheck current load eligibility/ceiling. CAS the booking to `SUBMITTING`, appending its intent event in the same record, then send once. Only the execution that wins and receives unambiguous acknowledgment of the fresh pre-send CAS may send. A timeout while acknowledging that CAS requires readback for diagnosis; seeing `SUBMITTING` does not authorize a send or resume. An ambiguous claim remains blocked/unknown unless exclusive ownership and absence of any prior send can be established. Never retry the whole SQL-to-TCP operation.
4. Save sanitized receipt and state plus their event in one booking-record update. Keep external state, local representative decision and conversation outcome as different facts. The dashboard reads booking truth from that record through the service, rather than trusting a separately copied `calls.booked` flag.
5. A crash between prepared call and booking insert leaves an explicit incomplete preparation. Recovery must fence a paused prior worker before aborting it: either establish that worker cannot resume, or first insert an aborted/tombstone attempt under the same deterministic intent primary key used by the original insert. If the tombstone wins, the stale insert cannot proceed. If it loses, inspect the existing booking and CAS only a pre-send state to failed; a stale sender's subsequent CAS must then fail. Never clear preparation merely because a SELECT found no booking. A potentially sent booking stays blocked. Release only after definitive no-send/rejection or authoritative resolution, never because a projection is missing or a deadline expired.
6. Project outboxes with idempotent inserts and bounded retries. Acknowledge projection only after durable insertion; prune only acknowledged events. Expose projection lag, queue size and failed receipts. Backpressure when bounded row/outbox capacity is approached; never silently discard activity.

There can still be temporary disagreement between aggregates and reporting projections. That lag must be explicit. State and its original audit event must agree atomically inside their authoritative aggregate. There is no exactly-once transaction spanning Twin and raw TCP: a crash after the send intent but before/during send leaves uncertainty. Conservatively retaining `UNKNOWN` protects against duplicate external effects while sacrificing automatic completion.

All Twin traffic should share a small, explicit scheduler with a bounded queue and priority for send intents/receipts over projections/dashboard reads. Operate below the observed rate limit, measure queueing, and document the supported concurrency. Do not add an unbounded retry layer. Twin query timeouts after writes require readback of the original key/revision, not an assumption that the write failed. Apps continues reading through authenticated service endpoints because the native gateway is known to fail.

## 6. Trade-offs and strongest argument against the verdict

| Storage alternative | Advantages | Failure/cost under the verified constraints | Assessment |
|---|---|---|---|
| Eight normalized tables, direct synchronous writes | Familiar relational queries, small records, easy exports | Independent state/audit updates can disagree; many statements consume shared capacity; repair logic still needed | Keep reporting shapes if useful, reject unspecified atomicity |
| Call/booking aggregates with same-record event outbox | Uses single-record atomic updates; state and original event cannot separate; fewer synchronous statements | Serialization, bounded record growth, CAS contention, projection lag and recovery need explicit handling | Preferred starting design for this constrained POC, conditional on supported SQL/limits |
| Append-only events with projected state | Reconstructable history and explicit ordering | Conditional sequence allocation, replay/versioning, uniqueness across calls/loads and projection traffic add machinery | Too much implementation/defense burden unless the actual system already uses it correctly |
| Transactional coordinator outside Twin, mirrored into Twin | Conventional state-plus-outbox transactions and constraints | Another datastore/deployment; Twin mirror can lag; violates native-default requirement unless the limitation is justified | Strong fallback if Twin aggregate/claim semantics cannot meet proven needs, not the first change |

The simplest normalized design would be preferable with a normal transaction boundary. The aggregate recommendation follows this API's demonstrated limitations. It does not imply that JSON is generally better than tables, nor that every event needs an event-sourcing framework.

Preserving one service reduces operational burden and keeps the call flow traceable. Moving only I/O out of business logic improves isolated reasoning without creating microservices. Keeping the pure parser despite CC 18 avoids replacing readable protocol checks with abstraction merely to improve a score. Retain a documented complexity exception while reducing orchestration complexity.

The pricing HMAC and per-load cap should be retained until confidentiality tests and business trade-offs are evaluated. The supplied randomized test demonstrates bounded offers for valid inputs and different outputs for different secrets. It does **not** prove that an observer cannot infer a useful ceiling range, especially when the gap band is public. Stronger secrecy can lose acceptable deals below the real ceiling; measure that cost and document what 'indirect disclosure' means for the challenge.

One-shot TMS submission intentionally prefers unresolved/reviewable inventory over duplicate bookings. No refactor can create cancellation, finalization or an external idempotency key. Representative confirmation is a separate local approval and cannot turn `PENDING` into `BOOKED`. A storage fallback can preserve evidence, but no application architecture can guarantee capture of a reply lost to a process/power failure before any durable write.

**Strongest argument against this verdict:** the actual working backend may already solve these failures and may have a storage model that is simpler than this proposal. It is absent from the permitted folder. Refactoring the phase 1 snapshot before obtaining that exact source could waste work, duplicate fixes and replace the only version that passed a real call. Therefore the first action is provenance/import and a second audit, not implementing the proposed tree. The demonstrated library defects justify targeted fixes to this library, not a confident rewrite judgment about unseen code.

## 7. Change order

No changes below were made during this audit. Each implementation step should have one assigned writer and a small reviewed commit; pushing remains subject to the owner's existing approval rule.

| Order | Smallest safe step | How behavior is preserved | Verification |
|---:|---|---|---|
| 1 | Obtain exact working backend, workflow/version, Apps source and deployment recipe; record their provenance | Imports tested artifacts rather than reimplementing a second system | Fresh isolated checkout reproduces the offline suite; every mandatory component has an identified file/version |
| 2 | Pin runtime/audit versions and add repeatable offline checks; scope the network guard | No business-result changes; test setup restores global state | Run on Python 3.12; original 112+7 cases retained; no external connection succeeds |
| 3 | Add regression cases for the ten findings before modifying behavior | Establishes exact accepted behavior and explicitly approved corrections | Failing probes cover save failure, cancellation, connect refusal, partial bytes, rep race, unknown confirmation, stale pickup and invalid negotiation/policy |
| 4 | Add concrete types and explicit store revision contracts; extract memory fake/policy loader only | Keep public response and protocol fixtures unchanged | Strict mypy passes incrementally, original fixtures and price vectors unchanged, no `Any`/ignore blanket |
| 5 | Correct neutral unknown output, unknown-confirm guard, rep CAS, pickup and negotiation invariants | Changes only invalid/ambiguous paths; future eligible/pending happy path remains | Sequential and genuinely interleaved tests; loser conflict; no excessive offer/rate/round; no past-pickup send |
| 6 | Preserve typed transport stage and bytes | Keep request framing, fresh connections and no write retry | Loopback tests for refused connect, reset before/after write, partial reply timeout and malformed framing; assert exact send count and evidence |
| 7 | Supervise send plus receipt save, add bounded durable evidence fallback and shutdown drain | Caller disconnect changes waiting behavior, not booking command count | Cancel at every await; fail receipt saves repeatedly; restart with persisted data; exactly zero or one fake send, no lost available receipt |
| 8 | Implement or repair the smallest authoritative storage boundary after reviewing actual SQL | Preserve call/booking identifiers and outcomes; treat old reporting rows as projections | Real process termination/restart against an offline durable backend; 20 contenders; failure after every SQL boundary; state/outbox agreement and no resend |
| 9 | Route the Apps UI through authenticated service reads, add lag/unknown-age indicators and bounded polling | Existing native UI remains; statuses retain their actual meaning | UI/API contract tests, credential isolation, zero Confirm on unknown, identical real/synthetic cohort totals |
| 10 | Reconcile docs, QA evidence and hand-in artifacts; do an owner walkthrough | Delivery reflects the exact reviewed artifact instead of an architecture aspiration | Cold build/deploy rehearsal with fakes; requirements checklist; owner explains each runtime file and failure path |

Historical booking commands must not be replayed as verification. Use sanitized replies, fake TMS and offline SQL/fault tests. Any later live demonstration is a separate owner-authorized activity with protected/spent inventory handled explicitly; this audit creates no such authorization or need.

## 8. Measurable acceptance gates for enterprise quality

The present snapshot fails the completeness, type-safety, durability and correctness gates. Passing unit tests and one real call are necessary evidence for limited paths, not a substitute for these gates.

| Gate | Required evidence |
|---|---|
| Complete, reproducible submission | Exact tested commit plus sanitized workflow/version, Apps source, reviewed schema/setup, Dockerfile and one deployment command; clean Python 3.12 build using pinned dependencies; all PDF page 5 deliverables present |
| Owner comprehension | An uninvolved mid-level engineer follows each runtime module's execution flow within 60 seconds using submitted code/references; the owner separately explains every submitted file and independently traces one HTTP tool request through authentication, trusted call state, SQL and response |
| Static contracts | Ruff with a pinned explicit rule set returns 0; `mypy --strict` returns 0 for runtime code and test helpers, no blanket ignored/untyped modules; no environment/file reads in core; no adapter/framework imports in core |
| Readable modules | Runtime modules normally at most 250 physical lines; orchestration functions normally CC at most 10; protocol parser's current CC 18 is a documented exception with exhaustive framing cases; exceptions require concrete readability evidence |
| Meaningful coverage | At least 95% production statement coverage and 90% branch coverage, excluding only tests/fakes/declarations with recorded reasons; every safety invariant below has a failure-injection test regardless of coverage percentage |
| Authorization and identity | Every exposed endpoint and action covered by unauthorized/wrong-role tests; trusted run ID supplied outside model arguments; cross-call substitution denied; FMCSA/OTP failures reveal no load details; caller input cannot set contact, budgets, offer or agreement price |
| OTP concurrency | Twenty simultaneous consumption attempts yield one winner; expiry, leading zeros, send/attempt limits, MC changes and replay tested; reset/resend cannot reset budgets; no expected code in agent output/logs |
| Price and round limits | Zero above-ceiling or above-policy-cap spoken/accepted/sent rates over seeded randomized and adversarial inputs; missing/invalid ceiling fails closed; max three counters across loads/MC changes and retries; policy validation rejects invalid configurations at startup |
| Atomic storage/audit | After failure at every persistence boundary, every committed authoritative revision has its original audit event in the same record; projection replay is idempotent; no duplicated rounds or consumed OTP without matching call revision; lag is visible rather than silently interpreted as absence |
| Booking concurrency/recovery | Twenty simultaneous contenders yield one active load claim and one active call claim; distinct worker/process tests and actual terminate/restart tests preserve blocks; for every timeout/crash schedule fake TMS observes at most one send per immutable agreement; no automatic resend on unknown or stale OPEN |
| Receipt and status truth | Proven no-send becomes failed; potentially sent remains unknown; available partial/complete reply is retained with sanitized stage/error/count/hash; injected save failure preserves recoverable evidence; unknown cannot be confirmed; PENDING and local rep approval never increment TMS-confirmed metrics |
| Bounded Twin usage | At the declared supported concurrency, all simulated reads/writes/projections/dashboard polls share a bounded scheduler below the observed roughly four statements/second limit; no unbounded queue/retry growth; voice-facing calls meet a documented deadline, initially at most 12 seconds before irreversible send; receipt completion survives caller timeout |
| Projection/review operations | Under healthy dependency conditions, p95 reporting lag at most 30 seconds at declared load; older lag triggers a visible warning; unknown bookings older than a configured SLA are reviewable; reconciliation never resends or clears uncertainty without authoritative evidence |
| Operational security and recovery | Secrets/ceilings/codes absent from captured voice responses and ordinary logs; ops credential remains server-side; redacted evidence sink has restricted access and tested restore; documented startup/shutdown/backup/recovery procedure demonstrated offline |
| QA and delivery truth | Documented standard/edge/adversarial scenarios tied to commit and workflow version; real and synthetic cohorts separated; numerator/denominator of each KPI testable from records; assignment assumptions and unresolved finalization stated in prospect/build/video material |

Where native SQL details cannot be established offline, record that gate as pending rather than substituting the in-memory fake. The verified 20-way primary-key result is accepted evidence for that primitive only. A later authorized platform check must use disposable non-booking rows and the actual schema/constraints; no live booking is needed to validate SQL coordination.

## 9. What could not be verified

- The actual working HTTP backend, workflow prompts/tool mappings, Apps source and deployment artifact. Their locations outside this folder were not opened. Consequently no claim is made about their current authentication, OTP enforcement, Twin writes, dashboard calculations or production defects.
- A full HTTP request to durable storage trace. Only the supplied Python booking path and its in-memory persistence were traceable and exercised.
- The owner-reported successful end-to-end call, eight spent loads, current platform state and gateway failure through fresh external evidence. Those are accepted constraints, not retested. Historical documents report earlier, different totals and are not a current inventory.
- Twin SQL syntax/features for the proposed aggregate/outbox, row-size limits, actual schema, indexes, active-call/load uniqueness, affected-row reporting, commit-after-timeout behavior and rate-limit recovery. No live SQL was sent.
- Production process restart, deployment overlap, real durable receipt fallback, shutdown draining, multi-worker behavior or backup restore. Existing recovery tests reuse in-memory state and do not establish those guarantees.
- Python 3.12 runtime behavior, Docker image contents, cloud deployability, dependency vulnerability status, performance under representative concurrency or deployed-host network latency. Tests ran on Python 3.14.0; mypy's 3.12 setting is not runtime verification.
- Real FMCSA authority interpretation, email delivery/contact ownership, OTP redaction, native scenario/adversarial outcomes, agent-initiated hangup or spoken mocked handoff for the submitted version.
- Actual TMS currency/scale, pickup timezone, complete field/status/rate grammar, reservation exclusivity, authoritative ownership recovery, pending lifecycle or finalization. No cancellation/idempotency capability is assumed. No final BOOKED outcome is claimed.
- The 60-second comprehension standard through an independent timed reader trial, or the owner's ability to defend every file. The assessment here is structural, not a measured human-comprehension result.
- Absolute resistance to indirect ceiling inference or arbitrary transcript/prompt attacks. HMAC variation and a repr exclusion are insufficient proofs, and the live agent/output boundary is absent.
- Repository reviewer invitations/privacy settings, prospect email, finalized build description, workflow link accessibility and walkthrough video. No external account was queried or message sent.
- The suggested book. It is outside the permitted folder and was not read or cited. The storage comparison is derived from inspected code, local requirements and the supplied interface constraints.

Only `AUDIT_REPORT.md` is intended as a new repository artifact. Existing source/reference digests and final Git status are checked before delivery. Temporary metrics/probes remain under `/tmp/happyrobot-audit.lynVua` and are not submitted application code.
