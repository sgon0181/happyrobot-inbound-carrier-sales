# Carrier Sales Prototype

Run started 1 November 2026 at 11:08 Sydney time. Base design: architecture v2.5,
commit `2d08ae1`. Implementation branch: `prototype/e2e`. This report records
the completed controlled test; remaining submission items are listed separately.

## 1. Status

The third owner voice call completed the real integration chain with explicit
booking permission: FMCSA, new Gmail code, load matching, three genuine counter
turns, a fresh load-and-total question, and one TMS send for LD01085 at 2950.
The complete receipt is ACK_PENDING, TMS PENDING, reference EME8U26DKEX5DESS.
The signed-in App recorded rep approval for this valid booking. That local
business decision did not change the external TMS status.

One presentation requirement failed on that call: actual speech was shortened
to "Transferring for review" and omitted the full review/simulation disclosure.
The full line was only a tool argument. A dedicated literal finish_handoff tool
replaces that generated speech. Its no-send checks and separate owner voice
check are recorded in docs/qa-results.md. This repair does not retroactively
change the original call assessment or require another booking.

The first call's unsafe LD01094 booking stays blocked for consent review.
The second call ended prematurely during a rate question and sent no booking.
Both failures and their fixes remain in the evidence. There are exactly two
live write intents in this prototype campaign, both with complete receipts.
All follow-up permissions are consumed. No new booking is authorized.

155 offline service tests pass. Main, the original workflow, ARCHITECTURE.md
and Questions.Md remain unchanged. Nothing was pushed to Tech-Challenge.
The real integration path is demonstrated, with the spoken repair assessed
separately. This is not a claim of production readiness or external BOOKED.

## 2. Latest real-call gate

| Architecture section 11 item | Latest result |
| --- | --- |
| Real voice call with active MC | Passed, MC 138328 |
| Fresh code received and entered by owner | Passed, Gmail SMTP |
| Carrier counters | Passed, three genuine counter turns, final total 2950 |
| Exact permission before submission | Passed, fresh canonical question and "Yes, please" in same session |
| Complete reference-bearing receipt | Passed, 97 bytes, ACK_PENDING/PENDING |
| Full neutral review and mocked-transfer speech | Failed on v9 real booking call; repaired and checked separately with no send |
| Agent ends voice session | Passed, native agent_hung_up |
| Twin record and App visibility | Passed, real call, consent proof and receipt |
| Rep approval through signed-in App | Passed for LD01085 only; TMS remains PENDING |

The earlier failed-consent booking is excluded from the successful tentative
handoff KPI and cannot be confirmed. A dashboard handoff flag measures workflow
intent and acknowledged consented bookings, not an independent speech grade.
The latest presentation defect is therefore tracked separately from that KPI.
Native messages and voice-node transcript establish text and timing evidence;
no claim of an independent acoustic interruption analysis is made.

## 3. Completed call and booking safety

- Workflow: https://platform.happyrobot.ai/deployments/yhcdrf4kne4j
- Dashboard: https://codex-lab-carrier-sales-v24.happyrobot.dev/
- Latest run: 112f1a4a-84f3-420f-bce4-d7f374b381d1.
- Latest session: e4daa9a5-049f-4ef3-826a-b21bde64d301.
- LD01085, Little Rock, Arkansas, to Albany, New York, dry van.
- MC 138328, total 2950, reference EME8U26DKEX5DESS.
- Email subject: Carrier Sales Prototype verification code.

Booking remains enabled in service configuration, but the durable campaign
ledger has no unconsumed permission. The numerical three-intent ceiling is not
permission for another send. Never reset the ledger, reuse a spent load or
resend a reference-bearing request. No cancellation or external finalization
operation has been established. The separate speech-check workflow has no HTTP,
booking or email action and consumes no load.

## 4. PDF requirements

| Requirement | Evidence and status | Label |
| --- | --- | --- |
| FMCSA active operating authority | Positive MC 138328 from Fly; inactive MC 872144 refused through native text tool | LIVE |
| Email code during the call before matching | Owner received and entered the new email code on the real voice call | LIVE |
| Lane and equipment matching | Deployed service selected an OPEN, future dry van and returned carrier-safe details | LIVE |
| Pricing ceiling and disclosure controls | Existing versioned policy reused; confidential fields omitted from tool responses; offline checks pass | SIMULATED |
| At most three counters per call | Durable budget checks pass; latest real call made three genuine counters | LIVE / SIMULATED |
| Tentative booking and mocked handoff | Valid consented PENDING booking and real rep approval; full spoken disclosure repaired in a separate no-send check | LIVE, presentation assessed separately |
| MC, load, rate, outcome and notes in Twin | Real call and receipt persisted; consent concern and redacted transcript included | LIVE |
| HappyRobot Apps operations UI | Signed-in Production dashboard shows the real call, PENDING reference and review flag; action verification recorded separately | LIVE / HYBRID |
| Graceful TMS faults | Fake TCP tests, receipt recovery and deadline checks pass | SIMULATED |
| Authenticated endpoints | 16 service routes and 2 App routes rejected missing credentials with 401; docs disabled; native app source auth checks pass | LIVE / SIMULATED |
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
    and the third real owner call subsequently proved fresh permission and a valid send.
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
    retained as failed evidence. The latest repair uses a dedicated fixed literal finish_handoff, with no
    message parameters or variable references, plus the existing authenticated
    close action. Refusals and outages retain finish_call. Its new focused
    checks mock all nine HTTP actions and inspect actual rendered messages.
    Historical outage and uncertainty checks used generated closing speech. The uncertainty fixture's consent grade
    failed because its static response bypasses preparation; it is not a clean
    full-flow pass. All twenty attempts and failures are retained.

## 6. T-1 through T-7

| Check | Answer gained |
| --- | --- |
| T-1 Twin coordination | LIVE fallback contention: 8 claims produced 1 winner; 8 conditional changes produced 1 winner; zero projection errors. SQL multi-write CTEs rejected. Contended median 10322.1 ms, p95 10756.4 ms, from the local host. Uncontended requests were about 0.35 s. |
| T-2 TMS money, ownership and finalization | Active MC 138328 received complete PENDING acknowledgements at whole rates 1075 and 2950. Inactive MC alone cannot explain all pending acknowledgements. Finalization, expiry and money semantics remain unproven. |
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

Exactly two live sends in this campaign, no unconsumed follow-up permission:

| Load | MC | Rate | Result | Disposition |
| --- | --- | --- | --- | --- |
| LD01094 | 138328 | 1075 | ACK_PENDING, TMS PENDING, reference 3PUHTGRJNDQ5EKMM | Blocked, awaiting caller-consent review, no resend |
| LD01085 | 138328 | 2950 | ACK_PENDING, TMS PENDING, reference EME8U26DKEX5DESS | Explicit consent passed, local rep confirmed, no resend |

Run `94ad9f38-1cc8-4f87-8bb7-af945c6b9563`, session
`64698f2c-e109-49c1-b99b-8444a8f1ebf9`. Send intent
`0140ec8c-0f0a-4297-bc11-cb083f2f04ae` reached send_started and write_drained.
The complete 97-byte response hash is
`12b164a333db0ebb71dcd5411aac27178a6580ffe6bb6a1aec934b65b0826b35`.
See [sanitized evidence](docs/prototype-evidence/live-call.json),
[receipt](docs/prototype-evidence/live-receipt.txt) and the branch's TMS contract.
The earlier synthetic API dry run used the same load with booking disabled;
its FAILED row has no write intent and is not another send.

The second receipt is also 97 exact bytes, SHA-256
17f2a4563d82ef3e3d3cb132482c8efb953cb3563990013e5834d0e776fe11e5.
Twin and the exported private journal agree byte for byte. See
[latest receipt](docs/prototype-evidence/v9-live-receipt.txt),
[real-call audit](docs/prototype-evidence/v9-real-call-audit.json), and
[post-approval readback](docs/prototype-evidence/v9-real-app-approval.json).
The receipt metadata records awaiting at export time; the later approval
artifact records confirmed. Neither historical capture was overwritten.

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
| Dialogue fix used by latest owner call | Tested Development v8: 01a19539-96cf-7ba7-9540-5f73ab12e4db. Production v9: 01a19550-bb92-7b91-87ca-b3af46e459f8, 4jnriljjqp4m | Three mocked regressions and real-endpoint synthetic consent test passed; 18-node parity and seven safe schemas verified |
| Native QA | Five enabled high-priority criteria, eight historical fully mocked scenario resources plus focused regression cases | Preserve definitions and outcomes before removing only these prototype resources |
| Speech-only QA | [CODEX LAB ONLY] Handoff speech check, workflow 01a19587-81b9-7a6e-9d22-ce155bee099a, slug uowlgrnsmx1s | Five nodes, zero HTTP actions; preserve evidence before owner-approved cleanup |
| Fixed handoff | Development v10, 01a19583-a481-724f-96af-1c34f9e9c7cf; promotion fork v11, 01a19592-7887-751f-85aa-4faba052b68c | Verify publication and executable parity in latest QA evidence |
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

The original unsafe receipt and review flag remain unchanged. The corrected
human voice call passed strict consent and produced the second receipt.
Rep approval is now proved for that valid record, with the original record
still blocked. The v9 speech defect and its later no-send repair are separate
facts. See docs/qa-results.md and the live-call audit.

Container journal export failed for the first call after automatic stop/start;
Twin retained its exact response. The latest call's journal was exported before
idle and matches Twin exactly. This does not prove durable capture across
machine replacement. Use external durable storage before production.

Latest validation: 155 Python 3.12 service tests passed. The unchanged mirrored
App previously passed production build and typecheck in a Node 22 container.
Eighteen deployed missing-credential checks returned 401. Native simulation
iterations include failures, and no blanket adversarial-suite pass is claimed.
Main is clean at 2d08ae1, and the preserved harness remains at 6ed7d4b.
No Tech-Challenge push, reviewer invitation, email or final submission was made.
Final video and submission-access work remain outside this controlled test.

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

The session ended with Fly restored to min_machines_running=0, auto-stop and
auto-start enabled on the same single 256 MB Machine. Receipts were exported
before idle. The same Machine was then explicitly stopped to save budget.
A new incoming request can auto-start it; this is not a hard spending cap.
[Final stored-state and host check](docs/prototype-evidence/final-no-send-check.json)
records two unchanged intents, no unused permission and the stopped host.
Production workflow v11 is the verified executable-equivalent
fork of tested v10, with the fixed handoff tool. The separate real owner speech
check passed; [voice evidence](docs/prototype-evidence/fixed-handoff-owner-voice.json)
and [promotion parity](docs/prototype-evidence/workflow-v10-v11-parity.json)
record its exact scope. No additional load was spent to repair speech.
