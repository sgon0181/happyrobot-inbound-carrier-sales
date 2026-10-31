# Platform Checks

Sanitized results from Codex's isolated end-to-end harness, 2026-10-31 (Australia/Sydney). The harness lives in a separate Codex worktree, outside this repository, so this file is the tracked record. It is not the production application, and it sent zero `LOAD_BOOK` requests.

| Check | Status | What happened | Next step |
|---|---|---|---|
| **T-1:** Twin coordination | Blocked | `SELECT 1` from a lab workflow returned `twin instance not available: record not found` in both staging and production. No tables exist. Uniqueness, atomic updates and latency are untested. | Provision Twin, then run T-1. Its Postgres fallback does not replace Twin. |
| **T-3:** code delivery and log exposure | Open | A native HappyRobot email action returned HTTP 202 and the message reached the candidate's Gmail inbox. The normal MCP workflow trigger returned Cloudflare HTTP 502 twice, so automatic delivery is unproven. Whether run details expose the code was not reported. | Test the trigger the service will really use, then check run details. |
| **T-4:** trusted call identity | Open | In a text session, `verify_carrier` reached the harness with the correct MC over an authenticated webhook. The harness issued its own private per-call token, which is the T-4 fallback. A trusted runtime call ID and stable operation ID are untested, and no real web voice call ran from MC collection through handoff. | Test with a real browser web call. |
| **T-5:** FMCSA access | Open | Direct requests from the local machine returned HTTP 403. A HappyRobot native HTTP node reached FMCSA for five MCs. Access from Fly.io is untested. | Test a direct request from Fly.io. A 403 is not inactive authority or a bad key. |
| **T-6:** ending a session | Open | Two full-workflow text scenarios reached the correct refusal of inactive MC 872144, then stayed open until the 1m30s scenario limit cancelled them. Both returned N/A, not a pass. An explicit end-call prompt instruction did not help, and the transcript shows no terminal tool. | Find how a workflow ends a session, then plan conversation tests around the time limit. |

## What the harness ran

- **Offline:** 60 Python tests covering TMS framing and failures with synthetic transports, OTP gating and expiry, matching, pricing protection, counter limits, HTTP authentication and per-call reservation idempotency. These are not live service calls.
- **Live reads:** `DEBUG_ECHO` authenticated, and a dry-van search returned 16 records, including `OPEN` and `PENDING`. Full reads returned 19 fields.
- **Combined flow:** saved FMCSA result, code generation, real email receipt, verification, live TMS search, one counter, agreement, simulated reservation, a duplicate request returning the same reference, then a mocked handoff.
- **Prompt tests:** three native HappyRobot tests passed: MC tool selection, refusal to bypass verification or disclose the ceiling, and refusal to claim a real booking.
- **Conversation scenarios:** two full-workflow text sessions ran. Both were incomplete, as T-6 describes.

**What the combined flow was not.** It was a hybrid, not a live voice call. Authority was replayed from a saved response, storage was SQLite, the reservation was simulated, and the Gmail connector withheld the code, so verification used the code the sender already knew. It proves backend handling plus delivery, not a person reading a code from their inbox.

## Lessons for the build

- **Tool Call Result:** field visibility is separate from HTTP success. Successful replies stayed hidden from the model until safe fields were explicitly exposed.
- **Tool authentication:** a passing tool-selection grade does not prove an integration works. One test passed while the endpoint call lacked usable authentication, so confirm the call reached the service.
- **Email sends:** do not silently retry an uncertain send.
- **Scenario tests:** a full-workflow scenario will not run without an enabled Northstar grader, and it is cancelled at 1m30s. A text session tests conversation flow, not audio.
- **Idempotency:** the harness protects repeated requests within one call. That is not an inventory lock across calls.

## Lab resources

Three unpublished workflows labelled `CODEX LAB ONLY`, under namespace `codex_lab_20261031`, remain on the platform: a Twin probe, an own-inbox OTP sender and a draft web call. Three prompt tests, one adversarial scenario and one lab-only grader also remain. None is the production workflow, no Twin tables were created, and the temporary server and tunnel are stopped. Their IDs are in the harness's `resources.json`.
