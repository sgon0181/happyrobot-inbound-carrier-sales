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
authorized retest.

## Checks completed

| Check | Result | Evidence level |
| --- | --- | --- |
| Python 3.12 service suite | 139 passed, 0 failed; local fake TCP only, external network blocked | SIMULATED |
| Receipt faults and durability behavior | Pre-send failure, partial/late receipt, save failure, duplicate suppression, restart/reconcile and cleanup checks passed in the suite | SIMULATED |
| Pricing and negotiation policy | Exact money, ceiling controls, round limits, repeat actions and stale selected agreement checks passed | SIMULATED |
| API policy gates | Authority/code gates, call-bound consumed code, resend/failure budgets, hidden identity injection and role separation passed | SIMULATED |
| New booking consent | Exact load and total question, fresh located anchor, explicit yes, interrupted/conditional answers, wrong/decimal amount and missing anchor checks passed | SIMULATED |
| Historical disputed dialogue replay | New gate rejects the price clarification before the recorded booking tool call | SIMULATED on LIVE evidence |
| Native consent adapter readback | Fetched actual completed run/session/messages and rejected consent, about 2477 ms from local host; zero TMS writes | HYBRID |
| Twin contention | Eight booking claims, one winner; eight conditional updates, one winner; zero projection errors | LIVE infrastructure, synthetic business records |
| FMCSA positive | MC 138328 passed from deployed Fly service and on owner call | LIVE |
| Ineligible carrier and urgency bypass | Native text tool called the service and refused inactive MC 872144; no code or loads returned | LIVE segmented conversation |
| Booking-off API flow | Real FMCSA, email submission, TMS search and negotiation; synthetic QA code proof; FAILED/live_booking_disabled, no write intent | HYBRID |
| Owner email/code | New email received and code successfully entered during actual voice call | LIVE |
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
| Native App forged session | Native builder reported 401/redirect checks; scoped source review verified platform token validation | SIMULATED / static review |
| Mirrored App build | Clean Node 22 container npm install, production build and typecheck passed | SIMULATED build |
| Independent review | Read-only core and App reviewers found no remaining blocker in the final scoped changes | Static review |

## Evidence

- [Real call record](prototype-evidence/live-call.json)
- [Exact receipt](prototype-evidence/live-receipt.txt), SHA-256
  `12b164a333db0ebb71dcd5411aac27178a6580ffe6bb6a1aec934b65b0826b35`
- [Native consent readback](prototype-evidence/consent-recheck.json)
- [Synthetic App action result](prototype-evidence/app-actions.json)
- [Deployed authentication checks](prototype-evidence/auth-checks.json)
- [Deployed source hash verification](prototype-evidence/deployed-code.json)
- [Twin contention result](prototype-evidence/twin-contention.json)
- [Booking-disabled integration result](prototype-evidence/deployed-flow-off.json)
- [Production dashboard screenshot](prototype-evidence/dashboard-review.png)
- [Sanitized published workflow snapshot](../happyrobot/prototype-workflow.json)
- Private raw platform pages and test/build logs remain ignored under secrets/.
  They contain privileged data and are not sanitized public exports.

## What has not been proved

- Corrected permission handling during a new live voice booking, including
  transcript availability while a session is active. The strict matcher may
  require re-asking when the platform adds speech or punctuation.
- Cause of PENDING, external BOOKED finalization, cancellation, expiry, full
  rate-format bounds, money scale or cross-token ownership.
- Production SMTP transport. The temporary native action-test notifier exposes
  expected codes in privileged notification records and needs replacement.
- Durable receipt capture across machine replacement or automatic stop/start.
  The container journal was unavailable, but Twin retained the full receipt.
- Every native conversation/adversarial scenario in architecture section 9.
  No-match, broker-only, load taken mid-call, voice leading-zero code, active
  call TMS outage and native ceiling extraction suites were not completed.
  Backend tests do not prove those spoken behaviors.
- Native Northstar criteria and a full reusable conversation test suite were
  not created in this timebox. The backend metrics and recorded checks are
  separate artifacts, not a claim those platform evaluation resources exist.
- Real rep approval on this call. It is deliberately blocked for consent
  review; synthetic action success does not satisfy that real clean-run item.
- AI sentiment/summary. The prototype labels its deterministic summary and
  reports sentiment as not_assessed.
- Native multi-table transactional Twin storage. The real contention result
  applies to the canonical JSONB CAS fallback, not normalized transaction SQL.

No test-all operation was run on the live booking workflow: that operation can
execute tools and side effects. The corrected version was configured, validated
by native publishing and exported without another real booking probe.
