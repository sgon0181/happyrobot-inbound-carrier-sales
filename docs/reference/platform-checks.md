# Platform Checks

Sanitized results from Codex's controlled experiment against architecture v2.4, 2026-10-31 (Australia/Sydney): harness commit `0e0451d`, design pinned to `51f8d80`. The harness lives in a separate Codex worktree, outside this repository, so this file is the tracked record. It is a lab, not the production application, and a historical record: where it says "still to prove", the later prototype may have proved it. Current state is in [open checks](decision-log.md#open-checks) and [lessons from the prototype](../history/lessons-from-prototype.md).

**LIVE** means the named real integration ran. **HYBRID** mixed real and synthetic parts. **SIMULATED** used fixtures or fakes. A native text test is synthetic even when its workflow and HTTP tools ran live.

| Check | Status | What happened | What remains |
|---|---|---|---|
| **T-1:** Twin coordination | Answered on probe rows | LIVE: 20 unique insert contenders and 20 version-conditional updates each produced exactly 1 winner. Insert median 688 ms, p95 732 ms; update median 376 ms, p95 740 ms, measured from the local machine. | The real schema and constraints, and latency from the deployed host. |
| **T-2:** booking contract | Open | LIVE: one active-MC send ended `UNKNOWN` with no receipt. The load then read `PENDING`. See [the evidence](../tms-contract.md#active-mc-attempt-on-a-real-call). | Q8 accepts the demonstrated PENDING handling. External finalization and ownership recovery remain technically unspecified. Currency, scale and bounds remain assumptions under Q3. |
| **T-3:** code delivery and log exposure | Fallback adopted | The normal workflow trigger returned HTTP 502 and the native hook 401. LIVE: the deprecated action-test route delivered a code that a person read back during a call, but two same-subject emails arrived a minute apart, and privileged run details can expose expected codes. | The service sends the email itself (D-3). Prove delivery through the chosen provider from the deployed host. |
| **T-4:** trusted call identity | Identity answered | LIVE: `current.run_id` reached the service outside model arguments. No native stable operation ID was found. The lab's request fingerprint froze repeated identical counters, and its private call token made a retried first tool or an MC correction fail with HTTP 403. | D-16 and D-17 replace those lab choices. Prove both in a native call. |
| **T-5:** FMCSA access | Answered | LIVE: a direct lookup from a Fly `iad` machine returned MC 138328 as eligible in about 3.6 s. The local machine still gets HTTP 403, which is an egress difference. | Recheck from the final host. |
| **T-6:** ending a session | Answered in text | HYBRID: the built-in `hr_builtin_tool__end_conversation` ended a native text session in 9 s, and its grader passed. An earlier 14 s session closed but its wrapper was inconclusive, so it does not count. | The agent hanging up in voice, and a spoken mocked transfer. Scenarios are cancelled at 1m30s, so full calls need testing by hand. |
| **T-7:** Twin API gateway | Blocked | LIVE: Twin Settings shows Database Available and API gateway Failed. An authenticated app read returned HTTP 503 with an HTML body. One Retry deploy also failed, and creating a deployment key did not help. Normal app reads use the signed-in user's token. | HappyRobot needs to restore it. The fallback is now the design ([D-30](decision-log.md)). |

## The live call

One person made one real 114-second browser call on the lab workflow. All 18 workflow nodes ran, including seven business tools and the post-call close. A node succeeding only means its HTTP call ran, not that the business outcome was good.

1. **Authority:** a fresh FMCSA check accepted MC 138328.
2. **Code:** the action-test route delivered a code, the person read it back, and the service recorded it consumed before allowing search.
3. **Search:** speech recognition misheard New Jersey, the agent clarified, and it offered LD01077, El Paso to Newark, dry van, 1,892 miles, at 3225.
4. **Agreement:** the person accepted the first offer, with no counter rounds. Fresh `OPEN`, pickup and ceiling checks passed.
5. **Booking:** one send ended `UNKNOWN`. A lab defect discarded the error type and the raw reply, so the failing step is unknown.
6. **Later reads:** LD01077 read `PENDING` at roughly 54, 320 and 1,408 seconds, never with a reference. One reconcile kept the booking `UNKNOWN`.
7. **Ending:** the agent said senior review was needed, then wrongly said the load was not booked. The person disconnected, so the agent hanging up and a spoken mocked transfer were not shown.

Twin stored the MC, load, agreed rate, `UNKNOWN` state, review flag, seven tool calls and a redacted transcript. That proves the path up to booking on a real call. It is not an acknowledged-booking pass.

## Where the PDF stands

| Result | Requirements |
|---|---|
| Passed in the lab | Authority check on tested carriers; refusal ending a call (text session); Docker and single-command deploy; a browser web call with no phone number. |
| Partial | Code during the call (fallback route); load match (one lane live); full load details; ceiling enforcement (simulated, plus a live rejected forged rate, with no live counter round); ceiling secrecy; counter limits; failed negotiation; tentative booking; mocked handoff; logging and Twin capture (one JSON row); TMS failure handling; northstar; adversarial voice tests; endpoint authentication. |
| Blocked | Operations view and actions in Apps (T-7). |
| Not run | Prospect email, build description, repository invitations, walkthrough. |

Endpoint authentication is partial because the custom service passed 20 live checks (18 routes rejected a missing key, cross-call substitution returned 403, a supplied booking rate returned 400), while the Apps template's `/api/health` answered publicly with 200.

The offline suite is 98 tests: 38 new v2.4 tests and 60 earlier regressions. They pass in the harness; they test the lab's code, not `service/`.

## Setup state

| Item | State | Confirmed by |
|---|---|---|
| Twin | Database Available, external SQL working, API gateway Failed | Codex |
| Lab API key `TestCodex1` | Owner-approved Editor role, which applies workspace-wide because tag scopes are off | Codex |
| Docker | Daemon runs. A Python 3.12 amd64 image was built and pushed, and `service/` tests pass in `python:3.12-slim` | Codex and Claude Code |
| Fly app `codex-e2e-lab-sg-20261031` | `iad`, zero machines, image and secrets retained | Codex |
| Chrome microphone | Worked on the live call | Codex |
| Claude Code HappyRobot MCP | Own OAuth login; live reads of the workspace and Inbound Carrier Sales passed | Claude Code |

## Lessons for the build

- **Evidence:** save the send's step, error and raw bytes before acting on a failure. The one thing the live call needed most was thrown away.
- **Uncertain outcomes:** avoid false denial as well as false confirmation. "Not booked" can be as wrong as "booked".
- **Closing a call:** a close flag, the words spoken, the session ending and a scenario grade are four separate facts.
- **Tool Call Result:** field visibility is separate from HTTP success. Successful replies stay hidden from the model until safe fields are explicitly exposed.
- **Tool authentication:** a passing tool-selection grade does not prove an integration works, so confirm the call reached the service.
- **Twin access:** Viewer cannot write, and creating tables through the API failed with it. The lab's table was created in the UI.
- **Time limits:** a per-read budget is not a request deadline. Search made several reads with no overall limit.
- **Transcripts:** the voice and text formats differ, and redaction must cover failed code attempts as well as the successful one.
- **Hosting:** Fly's trial logs stopped the machine after 5 minutes. The call was inside a fresh run, so this did not cause its failure.
- **Email sends:** do not silently retry an uncertain send.
- **Scenario tests:** a full-workflow scenario will not run without an enabled Northstar grader. A text session tests conversation flow, not audio.

## How the lab differed from the design

- **Storage:** eight logical maps in one JSON row, which proves the locking primitive, not the schema.
- **TMS reads:** sequential detail reads, with no overall search deadline.
- **Email:** the deprecated action-test route, with one instance at a time.
- **Rep actions:** the app wrote directly to Twin, a shortcut the product must not copy. Backend Confirm and Decline ran on two synthetic bookings in real Twin (HYBRID), and no app button was clicked.
- **Post-call:** a deterministic summary, with sentiment not assessed. The AI summary is not yet built or proven.
- **Pickup times:** treated as UTC, an assumption.

## Earlier harness run

Before this experiment, a first harness ran 60 offline tests, live TMS reads, three native prompt tests and two text scenarios. Its combined flow replayed a saved FMCSA result, used SQLite and simulated the reservation, so it proved backend handling plus email delivery, not a live call.

## Lab resources

These lab resources remain for owner review: Fly app `codex-e2e-lab-sg-20261031` (no machines), Twin table `public.codex_lab_20261031_state` with labelled synthetic records, and the labelled lab deployment key. All three original lab workflows are unpublished. The prototype workflow (`yhcdrf4kne4j`) and Handoff speech check (`uowlgrnsmx1s`) were also unpublished on 2026-11-04. The existing App slug `codex-lab-carrier-sales-v24` was reused for production; it is now Carrier Sales, Build 18, and is not a disposable lab App.
