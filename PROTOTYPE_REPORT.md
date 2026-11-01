# Carrier Sales Prototype

Run started 1 November 2026 at 11:08 Sydney time. Base design: architecture v2.5,
commit `2d08ae1`. Implementation branch: `prototype/e2e`. This report is being
completed during the controlled run; pending items below are not successes.

## 1. Status

The owner's real call passed FMCSA and the emailed code, matched LD01094,
countered from 1050 to 1075, received reference `3PUHTGRJNDQ5EKMM` with TMS
`PENDING`, spoke the neutral mocked transfer and ended with `agent_hung_up`.
Twin and the signed-in Production Apps dashboard show the call and receipt.
However, the agent submitted after a price clarification without explicit
booking permission. The clean run therefore FAILED consent. The real record
stays ACK_PENDING, awaiting review, with Confirm blocked and no further sends.
A backend consent gate and prompt correction passed offline tests, including
replay of the disputed conversation; no second live booking is claimed.
Main, the real workflow, ARCHITECTURE.md and Questions.Md were not changed.

Continuation: 154 offline service tests pass. Real active-session platform
reads rejected a clarification and accepted a later explicit yes during a
native simulated conversation with all business actions mocked. Gmail SMTP
accepted a new code email on a separate synthetic call. Five native Northstar
criteria and eight fully mocked conversation scenarios now exist. Terminal
speech and session-ending regressions are being assessed separately from
automated grades. A clean human voice call and real rep approval remain pending.
One follow-up authorization is now allocated to fresh load LD01085. No second
send is claimed before the controlled owner call completes.

The second owner call passed the new SMTP code and made two genuine counters,
but the agent ended while the caller asked the rate. All preparation results
were nonterminal and no booking was sent. The guard worked; dialogue failed.
The revised dialogue passed three fully mocked regressions and a hybrid test
through the actual consent endpoint, with no TMS submission. The failed hybrid
fixture setup is also retained. See docs/clarification-fix.md. Production is
now v9, matching tested Development v8. Another clean human retest is pending.

## 2. Clean-run gate

| Architecture section 11 item | Status |
| --- | --- |
| Real voice call with active MC | Passed, MC 138328 |
| Code arrives by email and is entered by the owner | Passed, actual owner entry verified |
| At least one carrier counter | Passed, one counter, 1050 to 1075 |
| Complete TMS reference with PENDING | Passed, one complete 97-byte receipt |
| Clear caller permission before booking | FAILED, price clarification was treated as permission |
| Neutral carrier wording | Passed in recorded transcript |
| Spoken mocked transfer | Passed in recorded transcript |
| Agent ends the session | Passed, native _hangup followed by agent_hung_up event |
| Complete Twin call record | Passed, 51 messages collected across two pages; codes redacted |
| Rep confirmation in Apps on the real call | Not passed, deliberately blocked for consent review |

Synthetic App Confirm and Decline passed through the real signed-in UI,
service and Twin. They do not replace the missing valid real rep approval.

This is useful integration evidence, not a fully passed business demonstration.
The owner's interruption report is direct user evidence. Text messages alone
cannot measure audio overlap, so no acoustic diagnosis is claimed.

## 3. Owner's original call script

- Web call: https://platform.happyrobot.ai/deployments/yhcdrf4kne4j
- Dashboard: https://codex-lab-carrier-sales-v24.happyrobot.dev/
- Give MC `138328`.
- Read the code from the newest `[CODEX LAB ONLY]` email generated after the
  original call started. That call used the historical temporary sender. New
  SMTP emails use the subject `Carrier Sales Prototype verification code`.
- The completed call requested a dry van from Massachusetts to Ohio and selected
  `LD01094`, Boston to Toledo. That load is spent and must not be reused.
- The owner asked for 25 more, producing the agreed total of 1075.
- Wait for the neutral senior-review line and spoken mocked transfer. Let the
  agent hang up; do not end the call manually.

Booking remains enabled in configuration, but the original authorization is
CLOSED after its first reference-bearing acknowledgement. The owner authorized
continuing toward a clean call. Its follow-up mechanism requires an appended
one-send permission for a freshly rechecked disposable load, with the exact
prior intent ledger preserved. One permission is now armed for LD01085 after a
fresh OPEN/future-pickup check. Other read-only alternatives are not allocations.
Every newly authorized real submission spends a disposable load. A spent load
is never reused, including after FAILED or UNKNOWN. No cancellation or
external finalization operation is invented.

## 4. PDF requirements

| Requirement | Evidence and status | Label |
| --- | --- | --- |
| FMCSA active operating authority | Positive MC 138328 from Fly; inactive MC 872144 refused through native text tool | LIVE |
| Email code during the call before matching | Owner received and entered the new email code on the real voice call | LIVE |
| Lane and equipment matching | Deployed service selected an OPEN, future dry van and returned carrier-safe details | LIVE |
| Pricing ceiling and disclosure controls | Existing versioned policy reused; confidential fields omitted from tool responses; offline checks pass | SIMULATED |
| At most three counters per call | Durable per-call budgets and retry-window checks pass offline | SIMULATED |
| Tentative booking and mocked handoff | Reference-bearing PENDING and spoken transfer recorded, but caller consent failed | LIVE, failed consent |
| MC, load, rate, outcome and notes in Twin | Real call and receipt persisted; consent concern and redacted transcript included | LIVE |
| HappyRobot Apps operations UI | Signed-in Production dashboard shows the real call, PENDING reference and review flag; action verification recorded separately | LIVE / HYBRID |
| Graceful TMS faults | Fake TCP tests, receipt recovery and deadline checks pass | SIMULATED |
| Authenticated endpoints | All 15 tested unauthenticated service routes returned 401; docs disabled; native app source auth checks pass | LIVE / SIMULATED |
| KPIs and QA | Separate cohorts; disputed call excluded from consented-handoff KPI; offline and native results in docs/qa-results.md | HYBRID |
| Docker and single-command deployment | Python 3.12 non-root image; make deploy deployed approved Fly app | LIVE |
| Web call with no phone number | Separate published web-call workflow; no number provisioned | LIVE |
| Prospect email, build document, video and reviewer invitation | Build description, email draft, demo script and checklist prepared; final video, sending and reviewer access pending | Draft / not submitted |

## 5. Deviations from v2.5

1. **Twin transaction fallback.** External SQL cannot create tables and rejects
   data-modifying CTEs because the gateway wraps statements. Native UI created
   eight business tables plus a primary-key claims table. The approved fallback
   uses a version-checked canonical JSONB row in `proto_calls`; the other rows
   are monotonic read models. They are not normalized atomic authoritative
   tables. Keep the storage interface, and revisit implementation when native
   multi-table transactions become available.
2. **Apps read fallback.** The native Twin gateway remained Failed after the
   single allowed retry. The approved T-7 fallback routes all reads and actions
   through the service. The app never writes directly to Twin.
3. **Runtime Twin key.** The owner explicitly approved reusing the existing
   Editor key. Its workspace-wide permission is not described as table-scoped.
4. **Email transport.** The first call used the temporary native action-test
   route behind the notifier interface. During continuation the owner privately
   configured Gmail SMTP. The deployed service accepted a new email through
   SMTP on a synthetic call. The second real owner call proved receipt and entry; the historical
   temporary route remains a fallback in code, not the active configured path.
5. **OTP in the API dry run.** The real email submission was exercised, then a
   known synthetic challenge was used only on a marked QA call. This proves the
   deployed gates and later integration path, not human receipt of that email.
   It is explicitly HYBRID, not a successful real voice call.
6. **Receipt durability.** Private local capture plus Twin and restricted log
   fallback retain evidence. Container files are ephemeral. They need export
   before replacement; a durable volume or object store is required for a
   stronger cross-machine guarantee.
7. **Post-call analysis.** Transcript collection and redaction are implemented.
   Summary is explicitly deterministic and sentiment is `not_assessed`; no AI
   summary or sentiment result is fabricated.
8. **Health checks.** Every HTTP endpoint requires a bearer key. Fly uses a TCP
   liveness check rather than putting an HTTP bearer key in tracked config.
9. **Repository scope.** The owner authorized the prototype branch rather than
   main for this run. Native App publishing uses its separate managed app
   repository. No Tech-Challenge Git push or PR is made.
10. **Conservative campaign budget.** A durable send reservation counts against
    the limit even if connection setup later fails before sending. This can
    spend fewer than the three authorized wire sends, never more.
11. **Explicit booking consent.** D-8's agreement-stage submission was too broad
    for this conversation. Price agreement and permission to submit are now
    separate. A live submission requires a new explicit affirmative response
    to the service's exact load-and-total question, checked using native
    platform messages, with message IDs and agreement version saved. Missing,
    interrupted, stale or ambiguous evidence blocks the send. The strict check
    can reject otherwise valid paraphrases and may need another question.
    Recommend adopting this distinction in the architecture, after review.
    Active native-session reads now pass against an actual in-progress
    simulated conversation. Clarification failed; a fresh explicit yes passed
    in about 1069 ms from the local host. All business actions were mocked,
    so corrected human voice permission and a new real send remain unproved.
12. **Post-call collection repair.** Native messages use numbered pagination.
    The collector now retrieves both pages and coalesces adjacent ASR fragments
    before redaction. The corrected 51-message transcript replaced the earlier
    incomplete/redaction-deficient projection. Privileged native logs and
    private evidence still contain original speech, so these are not public
    sanitized artifacts.
13. **Northstar consent filter.** The earlier close handler mechanically marked
    handoff intent. The KPI now additionally requires recorded booking consent
    and excludes the disputed call. Spoken transfer evidence is assessed
    separately, not inferred from the close flag alone.
14. **Immutable campaign accounting.** QA classification cannot relabel a
    call after a send intent or receipt exists. This prevents an analytics
    change from erasing spent-load accounting. A follow-up permission names
    one fresh load and the exact prior intent IDs, and is consumed atomically
    with the next intent. Cohorts never reset the send budget.
15. **Terminal speech.** Native simulations exposed missing finish/hangup calls
    and then a fixed-message rendering failure. Those failed versions are
    retained as failed evidence. The current Development version attaches
    AI-generated terminal speech to finish_call, with exact safe output-schema
    validation. Its outage and uncertainty checks rendered actual closing
    speech and both closing tools. The uncertainty fixture's consent grade
    failed because its static response bypasses preparation; it is not a clean
    full-flow pass. All twenty attempts and failures are retained.

## 6. T-1 through T-7

| Check | Answer gained |
| --- | --- |
| T-1 Twin coordination | LIVE fallback contention: 8 claims produced 1 winner; 8 conditional changes produced 1 winner; zero projection errors. SQL multi-write CTEs rejected. Contended median 10322.1 ms, p95 10756.4 ms, from the local host. Uncontended requests were about 0.35 s. |
| T-2 TMS money, ownership and finalization | Active MC 138328 received a complete PENDING acknowledgement at whole rate 1075. Inactive MC alone cannot explain all pending acknowledgements. Finalization, expiry and money semantics remain unproven. |
| T-3 Notification | Original owner call proved receipt and entry through the historical sender. Continuation deployed Gmail SMTP; the second owner call proved actual receipt and code entry. |
| T-4 Call identity and retries | Native rejection tool reached service with hidden runtime run ID. Five-second retry window and stale-acceptance selection regression tested offline. |
| T-5 FMCSA | Real positive response from deployed Fly service for 138328; native text tool refused 872144. |
| T-6 Session ending | Native _hangup call followed by final agent_hung_up event. Completed real session, spoken goodbye and mocked transfer recorded. |
| T-7 Native Apps | Gateway remained Failed after one retry. The approved service fallback rendered the actual call and receipt in signed-in Production. |

The deployed booking-off checks measured actual service durations of about
128 ms for health, 358 ms for authority, 2341 ms for code submission, 506 ms for
load search, 2337 ms for negotiation and 545 ms for the disabled booking result.
Some local synchronous clients waited on an unusable IPv6 connection before
IPv4 fallback. Those client delays are not reported as service processing time.

## 7. Load ledger

Exactly one live send in this campaign:

| Load | MC | Rate | Result | Disposition |
| --- | --- | --- | --- | --- |
| LD01094 | 138328 | 1075 | ACK_PENDING, TMS PENDING, reference 3PUHTGRJNDQ5EKMM | Blocked, awaiting caller-consent review, no resend |

Run `94ad9f38-1cc8-4f87-8bb7-af945c6b9563`, session
`64698f2c-e109-49c1-b99b-8444a8f1ebf9`. Send intent
`0140ec8c-0f0a-4297-bc11-cb083f2f04ae` reached send_started and write_drained.
The complete 97-byte response hash is
`12b164a333db0ebb71dcd5411aac27178a6580ffe6bb6a1aec934b65b0826b35`.
See [sanitized evidence](docs/prototype-evidence/live-call.json),
[receipt](docs/prototype-evidence/live-receipt.txt) and the branch's TMS contract.
The earlier synthetic API dry run used the same load with booking disabled;
its FAILED row has no write intent and is not another send.

Protected inventory was excluded: LD01086, LD01082, LD01081, LD01075, LD01077,
LD01023, LD01032, LD01036 and the voided control LD01069. The historical harness
records and their uncertainty were not rewritten.

## 8. Resources created or reused

| Resource | Identity and scope | How to scrap later |
| --- | --- | --- |
| Preserved harness branch | lab/harness-v24 at 6ed7d4b | Retain or archive after owner review; not removed in this run |
| Prototype worktree | prototype/e2e at ~/.codex/worktrees/e2e-prototype/Tech-Challenge | Archive only after exporting ignored evidence and secrets |
| Fly app reused | codex-e2e-lab-sg-20261031, iad, machine 84eee5dbdd0008 | Stop or remove only this prototype machine after evidence export and owner instruction |
| Workflow created | [PROTOTYPE] Inbound Carrier Sales, 01a19476-5384-704b-9c5e-569fd96f9adf, slug yhcdrf4kne4j | Unpublish this workflow only; original workflow remains untouched |
| Workflow versions | Original call v1: 01a19476-53ae-7412-a2b8-7f33d081b2c0, gsv5l16hqrln. Consent correction v2: 01a194ae-0d43-7970-84c7-69c591936a37, 8yspwmt9ftll | Retain snapshot and evidence before removing either version |
| Earlier continuation workflow | Tested v6: 01a194f6-2b5d-7919-87cc-4f0dbe8c2e88. Historical Production v7: 01a19503-e8c4-768a-aade-7bf67ff9c590 | Superseded after the owner's price-clarification call; preserve its failed dialogue evidence |
| Current dialogue fix | Tested Development v8: 01a19539-96cf-7ba7-9540-5f73ab12e4db. Production v9: 01a19550-bb92-7b91-87ca-b3af46e459f8, 4jnriljjqp4m | Three mocked regressions and real-endpoint synthetic consent test passed; 18-node parity and seven safe schemas verified |
| Native QA | Five enabled high-priority criteria, eight fully mocked scenario resources | Preserve definitions and outcomes before removing only these prototype resources |
| Twin prototype namespace | proto_carriers, proto_calls, proto_call_transcripts, proto_call_events, proto_otp_challenges, proto_negotiation_rounds, proto_bookings, proto_unmet_demand, proto_booking_claims | Export canonical state and captures before deleting any prototype table; do not delete lab tables |
| Native App reused | codex-lab-carrier-sales-v24, display Carrier Sales Prototype | Preserve source and evidence, then revert or remove only this app with owner approval |
| App source | Native source commit b2fd1638705e6cf4c25da0cac4073b89e1dac5e6, mirrored under ops-app; consent guard verified in Production | Source and config are tracked, no env files copied |
| Private keys | Fresh agent, ops, OTP-hash and pricing secrets, private env and approved stores only | Revoke or rotate specifically these prototype keys after review; no values are in this report |
| App ops key | Server-only OPS_API_KEY, Production and Preview, separately approved at action time | Remove only this app variable when scrapping |
| Local Docker config | Ignored secrets/docker-config, private file mode | Remove after registry credential expiry; global Docker settings were not changed |

## 9. Known bugs and disposition

Keep the tested pricing policy, strict parser, receipt classification, one-shot
booking path, durable CAS interface, retry window, call gates and two-key API.
Keep real and synthetic records separate.

Review canonical aggregate storage and remove the temporary mail fallback before
a production deployment. Replace deterministic post-call analysis with a tested
native AI step if required for the final architecture. Treat physical table
projections as potentially lagging, and use the canonical service API for
operator decisions. The native app template's existing ESLint circular-config
failure remains separate from its passing typecheck and production build.

The call exposed a real consent defect. Keep its receipt, failed assessment and
review flag. Do not convert it to a successful demo or force rep confirmation.
The new gate passes offline checks and rejects the historical clarification,
and active simulated-session checks, but needs a clean human retest before
claiming corrected voice behavior. No additional load was spent to test this fix.

Container journal export failed after automatic stop/start because the capture
file was no longer available. Twin still held the exact complete response,
which was exported and hash checked. Use external durable capture before any
production claim of restart-safe receipt recovery.

Latest validation: 154 service tests passed on Python 3.12. Mirrored App build
and typecheck passed in a Node 22 container. The host's npm was unusable because
of a missing Homebrew library; no system repair was attempted. A fresh source
export needs Next.js build before standalone typecheck to generate its ignored
next-env.d.ts. Eighteen deployed missing-credential checks returned 401.
Native App Confirm and Decline changed only clearly synthetic fixtures; the
real record and reference were checked unchanged. Two independent read-only
reviews found no remaining blocker in the scoped consent and App changes.
Five native Northstar criteria and eight conversation/adversarial scenario
resources now exist with all external actions mocked. Their iterations include
real failures; no blanket suite pass is claimed. Draft deliverables are linked
in docs/submission-checklist.md. Final video, email sending, reviewer access
and the corrected clean human call remain incomplete.

The dialogue-corrected workflow v9 is published in Production. Configuration
retains booking enabled, but the durable campaign gate blocks additional real
sends unless a separate exact-load authorization is appended. Only LD01085 is
armed for one additional controlled owner-call send.
Do not reset the ledger or treat remaining numerical budget as authorization.
The signed-in [dashboard](https://codex-lab-carrier-sales-v24.happyrobot.dev/)
shows the actual review warning. Full results are in
[docs/qa-results.md](docs/qa-results.md).
The platform required a separate fork to publish the tested Development version
to Production. The v8-to-v9 parity artifact records unchanged executable
configuration and topology. Parent configuration is completed before child
schema samples, preventing later parent updates from invalidating those samples.
Historical deployed hashes apply to the earlier checkpoint. The continuation
deployment was separately verified: six local/deployed runtime file hashes
match, authenticated health returns 200, SMTP is configured, and Twin still
contains exactly the original intent/reference with no follow-up permission.
The first SSH check found the Machine stopped; authenticated health woke it
and the subsequent source check succeeded. This proves auto-start and current
deployment, not removal of the trial's five-minute limit.
The preserved harness remains at 6ed7d4b, and main is clean at 2d08ae1.
Nothing was pushed to Tech-Challenge.

The owner clarified a USD3 total hosting budget. No volume, extra Machine,
prepaid credit or paid support plan was added. The owner completed card setup;
Billing lists a payment method on the same account that owns the server.
A continuous-runtime check passed: 373.91 observed seconds, VM uptime from
67.02 to 440.93 seconds, the same boot and instance throughout, with every
status check started. No health, TMS, email or booking action was used by
that hosting monitor. The five-minute interruption did not recur.
make warm is for active QA only and now starts an already-stopped Machine;
make idle restores the single Machine's auto-stop. This is a spending plan,
not a hard cap.
See docs/fly-session-budget.md for rates, idle storage and cleanup limitations.
