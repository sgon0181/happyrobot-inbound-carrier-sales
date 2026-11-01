# Prototype QA results, 2026-11-01

Branch `prototype/e2e`, based on architecture v2.5 at `2d08ae1`.
This is a controlled prototype report, not production certification.
See the [full report](../PROTOTYPE_REPORT.md) for deviations and resources.

## Result

The real integration chain worked through a reference-bearing PENDING receipt,
spoken mocked transfer, agent hang-up, Twin record and visible Apps dashboard.
The conversation FAILED caller consent: a price clarification was treated as
permission to submit. The owner reported being interrupted. Text evidence
supports the consent failure but does not measure audio overlap.

The real booking remains ACK_PENDING, reference `3PUHTGRJNDQ5EKMM`, awaiting
review. Confirm is blocked. No further live booking was sent. The clean-run
gate is not passed, and the corrected voice behavior needs a separately
controlled human retest. The owner authorized continuing toward that result,
and one exact-load permission is allocated to LD01085. No additional send is
claimed until that controlled call completes.

## Checks completed

| Check | Result | Evidence level |
| --- | --- | --- |
| Python 3.12 service suite | 154 passed, 0 failed; local fake TCP only, external network blocked | SIMULATED |
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
| Owner booking send | Exactly one send for LD01094 at 1075, complete 97-byte PENDING receipt and stored reference | LIVE |
| Owner conversation consent | FAILED: price clarification preceded submission without clear booking permission | LIVE |
| Neutral wording and mocked transfer | Spoken senior review and simulated transfer present in transcript | LIVE |
| Agent ending | _hangup tool followed by agent_hung_up event; run/session completed | LIVE |
| Transcript handling | Both numbered pages collected, 51 messages; adjacent code fragments coalesced and failed attempts redacted in stored projection | LIVE evidence / SIMULATED regression |
| Native Production App | Signed-in dashboard visibly shows real receipt, review reason, call notes and separate synthetic cohort | LIVE |
| App Confirm | Clicked only SYNTHETIC-APP-CONFIRM; rep decision persisted as confirmed, TMS state remained ACK_PENDING/PENDING | HYBRID |
| App Decline | Clicked only synthetic UNKNOWN probe; rep decision declined, state UNKNOWN, claim retained and needs_release review | HYBRID |
| Real record after App tests | Same reference and ACK_PENDING, awaiting rep, consent review retained, no success KPI | LIVE |
| Deployed authentication | 16 service routes and 2 App routes reject missing credentials with 401 | LIVE |
| Continuation deployment | Six runtime file hashes match local source; authenticated health 200, SMTP configured, original single intent/reference unchanged, no follow-up permission | LIVE read-only |
| Fly after card setup | 373.91 continuous observed seconds, VM uptime 67.02 to 440.93 seconds, same boot and instance, every state check started | LIVE infrastructure, no business calls |
| Native App forged session | Native builder reported 401/redirect checks; scoped source review verified platform token validation | SIMULATED / static review |
| Mirrored App build | Clean Node 22 container npm install, production build and typecheck passed | SIMULATED build |
| Independent review | Read-only core and App reviewers found no remaining blocker in the final scoped changes | Static review |
| Native evaluation resources | Five enabled Northstar criteria and eight conversation scenarios with all eight external actions skipped using mocks | LIVE platform / simulated business |

## Evidence

- [Real call record](prototype-evidence/live-call.json)
- [Exact receipt](prototype-evidence/live-receipt.txt), SHA-256
  `12b164a333db0ebb71dcd5411aac27178a6580ffe6bb6a1aec934b65b0826b35`
- [Native consent readback](prototype-evidence/consent-recheck.json)
- [Active native consent boundary](prototype-evidence/active-native-consent.json)
- [SMTP sender acceptance](prototype-evidence/smtp-check.json)
- [Twenty native conversation attempts](prototype-evidence/native-conversation-qa.json)
- [Eight reusable fully mocked definitions](../happyrobot/qa-scenarios.json)
- [Five native criteria](../happyrobot/northstars.json)
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

- Corrected permission handling during a new human voice booking. Active-session
  transcript reads and matcher boundaries are proved by native simulation,
  but human speech, interruptions and the complete corrected live path remain
  pending. The strict matcher may require another explicit question.
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
- Real rep approval on this call. It is deliberately blocked for consent
  review; synthetic action success does not satisfy that real clean-run item.
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
hybrid setup failure is preserved separately. Production v9 matches tested v8.
A clean human booking is still pending. See [the focused record](clarification-fix.md).
