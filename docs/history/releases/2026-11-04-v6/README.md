# Version 6 and service release 17

Verified read-only on 2026-11-04 at 02:22 UTC (13:22 Sydney). The owner approved the release and reports that Claude pushed main, deployed the service, then published Version 6. This record independently verifies the resulting state; it does not independently prove the ordering of those actions.

| Component | Verified state |
|---|---|
| GitHub main | `bf512aaae9d1ce6c21600bd2f4f744633ccc229b`, matching the checkout |
| Service | Fly release 17 complete; machine `185d26da3644d8` started in iad, TCP health check passing |
| Deployed source | All 28 runtime Python/policy files match the checkout byte-for-byte; [SHA-256 manifest](service-source-sha256.json) |
| Workflow | Version 6 (`alj9n98f66df`) production live and published, retaining 16 nodes |
| Prompt | Exact reviewed text, SHA-256 `287da98f14bd76fccb6c8846af01d9423b3424d86140fa540245b48fd57deef5` |
| Booking mode | `LIVE_BOOKING=false`, confirmed in runtime flags, authenticated snapshot and published App |
| Call cohort | `synthetic`, confirmed in runtime flags; no secret setting changed |
| Service reads | Authenticated health 200 and snapshot 200; missing-key POST /calls/ended returns 401 |
| Operations App | Native selector shows production Build 20; redesigned navigation and data render at the existing alias |

The HTTP probes ran inside the deployed container over loopback. The existing ops key was used without printing or committing it. Health reported TMS reachable through its read-only ECHO. No call, email, reservation decision, TMS booking, deployment, publication or secret change was initiated by this verification. Existing holds remain untouched.

[Machine-readable record](release.json) retains the release/image identity, observations and limits. The source comparison covers runtime source and policy, not a reproducible image or dependency attestation. The current checkout has 2919 runtime Python lines and 4613 App TypeScript/TSX lines; no production code changes in this documentation task.

## Evidence and limits

- [Native production Build 20 selection](app20-build.jpg) and [published overview](app20-overview.jpg) establish the App observation. Claude's release handover identifies source 48ba398/import 97da4f6, with the owner pressing Production. The 77-file source archive independently matches the current checkout. Exact production source bytes were not independently retrieved. Final read-only 1280px views/panels and clean-container frontend checks are recorded below. The earlier [Build 18 exact-source publication](../2026-11-04/README.md) remains historical evidence.
- Released bf512aa validation is 487 offline tests, actual 100% coverage over 1650 statements and 406 branches, business branches 256/256. The exact prompt passed 40 checkpoint definitions twice, 80/80 native grades. [Pinned evidence](../../../../happyrobot/history/qa-v6-audit-fixes.json) retains all results and the two full-text follow-ups.
- The latest 15 workflow runs listed at inspection contained no new human Version 6 call. The latest was the earlier mocked agreement `6f44e94b`. Do not count these simulations as post-release voice acceptance.
- Complete spoken _hangup._message delivery, proactive disconnect and callback/storage evidence remain open. No fresh LOAD_BOOK is needed to verify them.

## Owner voice checks on live Version 6

Use the [web-call demo](https://platform.happyrobot.ai/deployments/6oaskq84xpfc). Keep booking sends off and calls synthetic. Use offered loads with fresh service checks; lane availability and FMCSA results can change. The MC examples below come from Claude's release handover, not a new eligibility lookup in this verification.

| Check | Caller action | Required evidence |
|---|---|---|
| Refusal | Try MC 134652, expected ineligible in the handover | Follow the actual service result. On ineligible, explanation and goodbye are spoken in _hangup._message; agent_hung_up, without waiting or idle filler |
| Agreement | MC 138328, authorized emailed code, an available load, explicit acceptance | Service-approved load ID/rate, spoken mocked senior-rep handoff, thanks and goodbye, all delivered before agent_hung_up |
| Compound amount | Say "1600 and 25" before giving a complete total | Clarification and a caller reply precede negotiate; no partial-rate agreement |
| Repeated ask | Repeat the same clear ask above the quoted offer, before agreement | The returned unchanged offer is described as unchanged; no invented new/final status |
| Failed negotiation | Give distinct asks above each returned offer until negotiation_failed | Failure is saved, no transfer, truthful refusal/goodbye and proactive hangup. Identical asks do not consume another round |
| Time pitch | Listen to a pitch | Date/clock match the supplied display, in the form "November 7 at 7:36 PM Central (CST)", retaining the correct CST/CDT label |

Retain each run ID, failed attempts and reruns. Review transcript, tool arguments, audio completion, end reason and Twin-backed activity. A saved close record alone is not proof of spoken closing. Never copy an OTP or credential into the report. Existing synthetic reservations can be used for review without being released; releasing a hold remains an owner decision.

After the targeted voice checks: finalize reviewer access, review the regenerated build-description PDF, record the owner video and approve submission. Keep the cohort synthetic for the demo; changing it is optional and needs separate approval. Publication is complete; acceptance and submission are not.

## Final check before owner voice acceptance

The [frontend report](final-check/frontend-qa.json) records 39 passing tests, lint 0 errors / 3 warnings, clean build then typecheck and zero production dependency vulnerabilities. The [visual report](final-check/layout.json) records nine 1280x900 views with no page-level horizontal overflow, disabled Confirm, both detail panels, truthful pending receipt and working refresh. Screenshots are alongside those reports. No rep action was clicked.

The refreshed 3-page build-description PDF and candidate source archive are prepared under submission/ready-to-submit/, which is ignored rather than committed. [The short owner checklist](../../final-owner-checklist.md) gives the remaining calls, video and approvals.
