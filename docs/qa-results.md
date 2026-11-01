# Candidate QA results, 2026-11-01

The isolated candidate has 187 passing Python 3.12 service tests. Two actual owner
rehearsals completed through FMCSA, fresh email verification, matching, real
counteroffers and native booking consent, with zero booking rows or write intents.
The final owner call and App confirmation passed the nine-item gate on run
5783608f-d54b-4a5d-b028-89db98ae10ec. One new live send returned PENDING with
a reference. Bookings were disabled immediately after native completion, and
authenticated health verified off. No resend or second send followed.

## Current evidence

| Check | Measured result | Label |
| --- | --- | --- |
| Entity storage | Per-call/booking/OTP CAS, primary-key claims, frozen old control,110 entities verified with zero mismatches | LIVE infrastructure |
| Contention | 8 load contenders,1 winner;8 booking transitions,1 winner;8 independent call sequences overlap | LIVE infrastructure, synthetic records |
| Rehearsal | Two real calls,4200 ask countered at 3600,3625 later accepted; natural consent passed; no send | LIVE integration rehearsal |
| Conversation matrix | 17 cases, every actual rate argument matched; conditional answers and withdrawals did not advance submission | SIMULATED native conversation |
| Exact text checkpoints | Percentage calculation4320, unfinished/completed amounts, information question, confirmed price tool argument | HYBRID model generation with explicit service-auth denial |
| Neutral acknowledgment fix | Actual first "Yeah, go ahead" replay now passes across one exact "One moment"; question/answer/ignored IDs retained | SIMULATED replay of LIVE evidence |
| Final v17 standard QA | 11 cases; nine graders passed, two failed. One genuine urgency-close failure and one static uncertainty fixture with failed permission/counter grades | SIMULATED native conversation |
| Final focused v17 | Counter, true final offer and natural permission passed manual tool/wording checks; all ended natively | SIMULATED native conversation |
| Service authentication | 16 routes, missing and wrong-role keys, all32 checks rejected 401 | LIVE auth boundary |
| App authentication | Six routes, missing and forged sessions, all 12 checks rejected or redirected as expected | LIVE auth boundary |
| Deployed file hashes | 34 runtime/policy/requirements files match the selected code commit | LIVE read-only |
| Final owner run | One live send, valid natural consent, 97-byte PENDING receipt, full handoff, native end and owner App approval | LIVE same run |

Read [conversation coverage](conversation-coverage.md) for exact nuances and
partial-run limits. Grades do not substitute for actual arguments or real service
execution. Every fully mocked native test had all nine HTTP skip overrides read
back before launch and verified in its actual snapshot. The deterministic custom
eval checkpoints use an explicit invalid key; their proposed tool calls are denied
before business logic, and the dummy call remains absent.

## Final same-run evidence

Run `5783608f-d54b-4a5d-b028-89db98ae10ec`, Production v17, passed exactly the
nine required items. Its first request for 4200 received a genuine 3600 counter;
the next 3625 proposal was clarified and accepted. The final exact question was
followed by "Yeah. Go ahead." The original question/answer IDs and session are
stored with the agreement. The owner attested to the full fixed sentence and
native hangup, then clicked Confirm for LD01062 in the signed-in App.

The single 97-byte reply is PENDING, reference 9HH6VP5Q2LQ09GCO. Its exported bytes,
Twin diagnostic hash and final stored booking match. Rep approval remains local;
the TMS is still PENDING. Complete v3 transcript storage retains the caller's own
MC while masking the code. [Final proof](prototype-evidence/candidate-clean-run.json),
[receipt](prototype-evidence/candidate-live-receipt.txt) and
[App readback](prototype-evidence/candidate-app-confirmed-row.png).

The first affirmative was followed by unmarked "Alright" speech, which
failed closed in the conservative proof matcher and caused an unnecessary repeat. The
second natural answer passed. The agent added a brief goodbye after the fixed
handoff, contrary to the prompt's instruction to add no speech. These quality
issues remain visible. Do not widen filler acceptance without a bounded replay
and rejection tests. No extra intent or send occurred.

The earlier preapproval export candidate-owner-final-call.json has null fields
named external_status and raw_reply_sha256 because those are obsolete projection
names. Its generic sanitizer also masks MC digits. This is an export limitation,
not missing TMS evidence. The authoritative final proof uses tms_status and
diagnostic.response_sha256 and checks the actual stored v3 transcript.

## Owner call while bookings were off

The owner later completed call `bde0340f-15d9-4dab-b7b1-c7e68cfbce98`
after the earlier live window had closed. The service returned
`not_booked` with `reason: booking_disabled`. No booking row or write intent
was created, and no TMS booking was sent. This was a mode-timing mismatch,
not a rejected TMS booking. The observed speech clearly rejected 4200 with a
3600 counter and clarified "3600 and 25" as 3625 before submitting that rate.
The owner was informed before opening a fresh, authenticated live window.
[Call evidence](prototype-evidence/candidate-owner-call-disabled.json).

## Remaining failure and limits

The urgency test refused an ineligible caller and exposed no loads or rates, but
spoke a goodbye without finish_call or native hangup. It idled about 66 seconds
before session closure. This is a genuine closing-protocol failure for review.
The final eligible-call gate passed independently on the actual owner run above.

Uncertainty reached the full fixed handoff and native end, but its static
senior_review fixture bypasses the real permission transition. Its failed grades
remain visible and are not called a full-flow pass. Some language traces hit a
harness backstop after proving only their observed phase. A simulator also
replaced one percentage request with its numeric equivalent; exact checkpoints
supply that missing input coverage. Preserve these distinctions.

The service uses authoritative entity rows, SMTP only and off/rehearse/live modes.
Older run restrictions and the aggregate-row design below are historical. The
App's saved name/alias changed, but its newer candidate source publish was canceled
because native Production deployment merges the separate App branch into main.
The existing functional App remains deployed. LD01094 stays blocked from Confirm.

## Current artifacts

- [Storage cutover](storage-cutover.md)
- [Final standard scenarios](prototype-evidence/candidate-v17-native-qa.json)
- [Fully mocked final-version fixtures](../happyrobot/qa-scenarios-candidate-v17.json)
- [Final focused scenarios](prototype-evidence/candidate-v17-focused.json)
- [Conversation matrix](prototype-evidence/candidate-v16-conversation-matrix.json)
- [Exact checkpoints](prototype-evidence/candidate-v17-exact-checkpoints.json)
- [Actual consent replay](prototype-evidence/candidate-neutral-acknowledgement-replay.json)
- [Service auth](prototype-evidence/candidate-auth-service-final.json)
- [App auth](prototype-evidence/candidate-auth-app-final.json)
- [Published configuration](prototype-evidence/candidate-v17-executable-parity.json)
- [Runtime hashes](prototype-evidence/candidate-runtime-hashes-dd57d54.json)
- [Unused live window safely off](prototype-evidence/candidate-unused-live-window-off.json)

## Final deployment and shutdown

The post-call exclusion policy was deployed with bookings off. All 34 checked
runtime/policy/requirements hashes match commit dd57d54; subsequent delivery
changes are documentation and evidence only. Their final Git blobs are compared
with these observed deployed hashes before handoff. Authenticated health verified
off, the original call/load claims remain active, and the final booking remains
ACK_PENDING with rep_decision confirmed. make idle completed and the same single
Fly Machine was explicitly stopped and read back as stopped. No new resource or
second booking was created.

A later rep_decline event on the older LD01094 record was observed at 10:22:02 UTC.
It now has rep_decision declined, review_required true and reason needs_release.
Its original receipt, intent and ACK_PENDING state remain retained. No agent rep
action or TMS release was performed. The original consent-review evidence remains
preserved, and the load remains blocked. This event does not change the final
LD01062 approval or the one-send result.

[Environment readback](prototype-evidence/candidate-final-environment.json),
[stopped Machine](prototype-evidence/candidate-final-machine.json), and
[exact new row inventory](prototype-evidence/candidate-final-resource-inventory.json).
The pre-call and post-call byte observations are separate: the voice call ran
c25f66b; the later runtime differs only by the spent-load exclusion and its JSON
formatting. Pricing numbers and fixed handoff text are unchanged.

## Historical prototype checkpoint

The following material is preserved as earlier evidence. Its deployment state,
permissions, test counts and next steps are superseded by the candidate section
above and PROTOTYPE_REPORT.md. It is not a current instruction to enable bookings.

# Prototype QA results, 2026-11-01

Branch `prototype/e2e`, based on architecture v2.5 at `2d08ae1`.
This is a controlled prototype report, not production certification.
See the [full report](../PROTOTYPE_REPORT.md) for deviations and resources.

## Result

The third real owner call passed authority, fresh Gmail code entry, matching,
three genuine counter turns and strict booking permission. One send for LD01085
at 2950 returned ACK_PENDING/PENDING, reference EME8U26DKEX5DESS. The signed-in
App saved a local rep confirmation, while TMS stayed PENDING. Exactly two live
write intents exist across this prototype campaign, with no unused permission.

That call failed the full spoken review/simulation disclosure. Its actual
closing speech was shorter than the tool argument. The repair uses a literal,
uninterruptible finish_handoff message with no variable or message argument.
Two no-send native text checks verified rendered handoff/outage behavior.
The owner completed the isolated speech-only call and reported the full line
and automatic hangup. Native voice evidence is recorded separately below.
These later checks do not retroactively turn the original call into a flawless
single-run demonstration.

The first LD01094 receipt remains in caller-consent review, with Confirm blocked.
The second owner call sent nothing and exposed a dialogue failure. Historical
failures, setup failures, inconclusive wrappers and failed grades are retained.
Main and the original workflow were not changed. No further booking is needed.

## Checks completed

| Check | Result | Evidence level |
| --- | --- | --- |
| Python 3.12 service suite | 155 passed, 0 failed; local fake TCP only, external network blocked | SIMULATED |
| Receipt faults and durability behavior | Pre-send failure, partial/late receipt, save failure, duplicate suppression, restart/reconcile and cleanup checks passed in the suite | SIMULATED |
| Pricing and negotiation policy | Exact money, ceiling controls, round limits, repeat actions and stale selected agreement checks passed | SIMULATED |
| API policy gates | Authority/code gates, call-bound consumed code, resend/failure budgets, hidden identity injection and role separation passed | SIMULATED |
| New booking consent | Exact load and total question, fresh located anchor, explicit yes, interrupted/conditional answers, wrong/decimal amount and missing anchor checks passed | SIMULATED |
| Historical disputed dialogue replay | New gate rejects the price clarification before the recorded booking tool call | SIMULATED on LIVE evidence |
| Native consent adapter readback | Fetched actual completed run/session/messages and rejected consent, about 2477 ms from local host; zero TMS writes | HYBRID |
| Active native-session consent boundary | While the actual native session remained in progress, clarification was rejected twice and a later explicit yes passed in about 1069 ms; all business actions mocked | HYBRID |
| Same-session and pagination contract | Numbered pages, timestamp ordering, wrong-session data, cross-session continuation and absent evidence fail closed | SIMULATED |
| Follow-up authorization | Exact-load permission and immutable prior-intent baseline, single consumption, three-intent cap and cohort bypass protection passed | SIMULATED |
| Workflow fork input bindings | Current node IDs are resolved by name; HTTP parameter groups use stable tool persistent IDs | Static contract check |
| Model-visible output schema | Custom-output refresh must reach exactly the 16 approved fields; stale error-only, incomplete, unknown or unvalidated fields fail closed without visibility writes | SIMULATED / LIVE configuration |
| Twin contention | Eight booking claims, one winner; eight conditional updates, one winner; zero projection errors | LIVE infrastructure, synthetic business records |
| FMCSA positive | MC 138328 passed from deployed Fly service and on owner call | LIVE |
| Ineligible carrier and urgency bypass | Native text tool called the service and refused inactive MC 872144; no code or loads returned | LIVE segmented conversation |
| Booking-off API flow | Real FMCSA, email submission, TMS search and negotiation; synthetic QA code proof; FAILED/live_booking_disabled, no write intent | HYBRID |
| Owner email/code | New email received and code successfully entered during actual voice call | LIVE |
| Gmail SMTP replacement | Owner supplied app password privately; deployed sender accepted a new code email on a synthetic call; the second real owner call then proved receipt and entry | LIVE transport and human entry |
| First owner booking send | Exactly one send for LD01094 at 1075, complete 97-byte PENDING receipt and stored reference | LIVE |
| First owner conversation consent | FAILED: price clarification preceded submission without clear booking permission | LIVE |
| First call neutral wording and mocked transfer | Spoken senior review and simulated transfer present in transcript | LIVE |
| Agent ending | _hangup tool followed by agent_hung_up event; run/session completed | LIVE |
| Transcript handling | Both numbered pages collected, 51 messages; adjacent code fragments coalesced and failed attempts redacted in stored projection | LIVE evidence / SIMULATED regression |
| Native Production App | Signed-in dashboard visibly shows real receipt, review reason, call notes and separate synthetic cohort | LIVE |
| App Confirm | Clicked only SYNTHETIC-APP-CONFIRM; rep decision persisted as confirmed, TMS state remained ACK_PENDING/PENDING | HYBRID |
| App Decline | Clicked only synthetic UNKNOWN probe; rep decision declined, state UNKNOWN, claim retained and needs_release review | HYBRID |
| First real record after synthetic App tests | Same reference and ACK_PENDING, awaiting rep, consent review retained, no success KPI | LIVE |
| Deployed authentication | 16 service routes and 2 App routes reject missing credentials with 401 | LIVE |
| Continuation deployment | Six runtime file hashes match local source; authenticated health 200, SMTP configured, original single intent/reference unchanged, no follow-up permission | LIVE read-only |
| Fly after card setup | 373.91 continuous observed seconds, VM uptime 67.02 to 440.93 seconds, same boot and instance, every state check started | LIVE infrastructure, no business calls |
| Native App forged session | Native builder reported 401/redirect checks; scoped source review verified platform token validation | SIMULATED / static review |
| Mirrored App build | Clean Node 22 container npm install, production build and typecheck passed | SIMULATED build |
| Independent review | Read-only core and App reviewers found no remaining blocker in the final scoped changes | Static review |
| Native evaluation resources | Five enabled criteria; historical scenarios mock all eight then-existing HTTP actions; new v10 checks mock all nine | LIVE platform / simulated business |
| Latest real booking permission | Fresh exact load/2950 question and explicit yes, same session and agreement proof; earlier ambiguous answer rejected | LIVE |
| Latest real send and receipt | LD01085 at 2950, 97 complete bytes; Twin and private journal exports match exactly | LIVE |
| Latest real rep approval | Signed-in App Confirm saved confirmed for LD01085 only; TMS stays ACK_PENDING/PENDING; original unsafe record still blocked | LIVE |
| Latest real spoken handoff | FAILED full disclosure: actual speech was shortened; the full sentence existed only in a tool argument | LIVE failure |
| Fixed handoff and outage | Two native targets completed with correct rendered messages, tool choice and native end; all nine HTTP actions skipped | SIMULATED conversation |
| Isolated owner speech check | Owner reports full fixed review/simulation line and automatic hangup; five-node workflow has no HTTP, booking or email action | LIVE voice, no business integrations |

## Evidence

- [Fixed handoff text checks](prototype-evidence/v10-fixed-handoff-text.json)
- [Separate owner voice check](prototype-evidence/fixed-handoff-owner-voice.json)
- [v10-to-v11 promotion parity](prototype-evidence/workflow-v10-v11-parity.json)
- [Final no-send and stopped-host check](prototype-evidence/final-no-send-check.json)
- [Latest real-call audit](prototype-evidence/v9-real-call-audit.json)
- [Latest exact receipt](prototype-evidence/v9-live-receipt.txt), SHA-256
  17f2a4563d82ef3e3d3cb132482c8efb953cb3563990013e5834d0e776fe11e5
- [Latest receipt metadata](prototype-evidence/v9-live-receipt.json), awaiting at export
- [Later real rep-approval readback](prototype-evidence/v9-real-app-approval.json)
- [Rep-approved dashboard](prototype-evidence/v9-real-rep-approved.png)

- [Real call record](prototype-evidence/live-call.json)
- [Exact receipt](prototype-evidence/live-receipt.txt), SHA-256
  `12b164a333db0ebb71dcd5411aac27178a6580ffe6bb6a1aec934b65b0826b35`
- [Native consent readback](prototype-evidence/consent-recheck.json)
- [Active native consent boundary](prototype-evidence/active-native-consent.json)
- [SMTP sender acceptance](prototype-evidence/smtp-check.json)
- [Twenty native conversation attempts](prototype-evidence/native-conversation-qa.json)
- [Eight reusable fully mocked definitions](../happyrobot/qa-scenarios.json)
- [Historical v9 criteria](../happyrobot/northstars.json)
- [Current v11 criteria](../happyrobot/northstars-v11.json)
- [Tested-to-Production workflow parity](prototype-evidence/workflow-v6-v7-parity.json)
- [Current v8-to-v9 parity](prototype-evidence/workflow-v8-v9-parity.json)
- [Synthetic App action result](prototype-evidence/app-actions.json)
- [Deployed authentication checks](prototype-evidence/auth-checks.json)
- [Deployed source hash verification](prototype-evidence/deployed-code.json)
- [Continuation deployment verification](prototype-evidence/continuation-deployed-code.json)
- [Fly runtime verification](prototype-evidence/fly-post-card-uptime.json)
- [Twin contention result](prototype-evidence/twin-contention.json)
- [Booking-disabled integration result](prototype-evidence/deployed-flow-off.json)
- [Production dashboard screenshot](prototype-evidence/dashboard-review.png)
- [Sanitized workflow snapshot](../happyrobot/prototype-workflow.json), inspect its
  version and environment before assuming it is the Production deployment
- Private raw platform pages and test/build logs remain ignored under secrets/.
  They contain privileged data and are not sanitized public exports.

## What has not been proved

- Cause of PENDING, external BOOKED finalization, cancellation, expiry, full
  rate-format bounds, money scale or cross-token ownership.
- The temporary action-test notifier remains in code as an inactive fallback.
  New Gmail SMTP receipt and human code entry are proved by the second owner call.
- Durable receipt capture across machine replacement or automatic stop/start.
  The container journal was unavailable, but Twin retained the full receipt.
- Every native conversation/adversarial case in architecture section 9.
  Eight fully mocked resources now cover refusal under urgency, no match,
  failed-code bypass, TMS outage, exhausted negotiation, ceiling extraction,
  neutral uncertainty handoff and consent readiness. These include failed
  iterations, not a full passing suite. Broker-only, load taken mid-call,
  voice leading-zero codes and live fault behavior remain uncovered.
- AI sentiment/summary. The prototype labels its deterministic summary and
  reports sentiment as not_assessed.
- Native multi-table transactional Twin storage. The real contention result
  applies to the canonical JSONB CAS fallback, not normalized transaction SQL.

No test-all operation was run on the live booking workflow: that operation can
execute tools and side effects. Targeted native simulations explicitly mock
every HTTP action, including post-call close, before execution. Automated
grades, scenario wrapper status, actual rendered assistant content and closing
tools are assessed separately. The fixed-message v5 said <no-value> despite
some passing grades and is not acceptable evidence of correct speech.

The earlier v6 Development correction uses an AI tool message tied to the closing
action. Two targeted checks verified actual rendering and both closing tools:

| Case | Actual terminal behavior | Automated result and limit |
| --- | --- | --- |
| TMS unavailable | Explained the outage, said goodbye, finish_call and native hangup, 24 seconds | Passed, wrapper completed |
| Neutral uncertainty handoff | Complete neutral senior-review and simulated-transfer sentence, finish_call and native hangup, 38 seconds | Explicit-permission criterion failed; wrapper inconclusive/backstop. The static mock returns senior_review during preparation, so this is a wording/end check, not a consented-flow pass. |

Both had no <no-value> rendering and mocked every external business action.
The twenty-run artifact preserves historical failures, criteria and wrapper
states. No further real booking probe was used to develop these changes.

Historical Production v7 was an unchanged executable fork of tested Development v6.
All eighteen node configurations/topology and seven exact safe output schemas
were checked before publication. This supports configuration promotion, not
a claim that the twenty historical attempts all ran on v7 or passed.

## Off-script call and corrected dialogue

The second owner call passed authority and the new SMTP code, then ended
prematurely during a rate question. It sent no booking. Three subsequent native
regressions and the real-endpoint synthetic permission test passed; one earlier
hybrid setup failure is preserved separately. At that checkpoint, Production
v9 matched tested v8. The third owner call subsequently passed real consent and booking, with a separate spoken-disclosure defect. See the latest audit above and [the focused history](clarification-fix.md).

## Fixed handoff checks

Development v10 uses finish_handoff only for senior_review. The full text is
literal, uninterruptible and identical in the separate speech-only workflow.
finish_call remains for refusals, outages, test-only outcomes and clear goodbyes.
The booking, consent and pricing implementation did not change for this fix.

| Focused v10 case | Manual rendered-message result | Automated status and limit |
| --- | --- | --- |
| Senior review | Complete exact line, finish_handoff once, no finish_call, native end, no extra speech | Target and wrapper completed; handoff grade passed, overall grade failed the explicit-permission criterion because the static fixture bypasses confirmation_required. Presentation-only proof. |
| TMS outage | Actual outage explanation and goodbye, finish_call once, no finish_handoff, native end | Native target completed and grader passed; outer wrapper inconclusive with scenario_backstop_elapsed. No repeat. |

All nine HTTP actions were read back as skip_execution_with_mock_output before
each run. Zero business HTTP calls or booking sends executed. Automated grades,
wrapper status and manual transcript assessments are distinct evidence.
The owner speech-check workflow cannot reach the service or TMS and does not
enter the brokerage's call KPIs. No new MC or booking experiment was performed.

The separate real voice check passed on run
015a290e-1f34-4ef6-b4cb-504b1f331617, session
fa14e28c-1d3d-4026-a826-36d6ae55f7f6. Native voice-node transcript and session
messages record the exact complete fixed line, a noninterrupted speech record,
a brief native Goodbye, and agent_hung_up. The owner independently reported
hearing the full line and hangup. The auditing agent did not independently
listen to the audio recording. This is voice presentation proof, not another
TMS integration or booking call.

Production is now v11, 01a19592-7887-751f-85aa-4faba052b68c, slug mhem72kctfhe.
All 20 executable nodes and topology match tested Development v10. All eight
tools expose exactly the approved 16-field schema; there are nine HTTP actions.
No booking, consent, price policy or service runtime change was needed for this
speech-only fix. Original v9 business-call evidence remains version-labelled.
