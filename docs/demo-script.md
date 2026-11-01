# Five-minute business walkthrough

Recording readiness: real consented booking and App approval are available.
The final walkthrough has not been recorded. Use the completed real-call
recording and the separate speech-check evidence, clearly identified.
No further live booking is allocated. Do not present a simulation as a new
booking or imply the original call spoke the corrected disclosure.

| Time | Show and say |
| --- | --- |
| 0:00-0:30 | Explain missed calls, repeated verification and inconsistent negotiation. Show the web-call entry and describe the first leg the agent owns. |
| 0:30-2:50 | Show the recorded real call: active MC, emailed code, matching lane, counters, exact total and explicit permission. Redact the code in audio and screen. Explain its shortened transfer disclosure, then show the separate fixed-speech check; no new booking. |
| 2:50-3:50 | Open the real call in Apps. Show load, MC, agreed rate, receipt and actual PENDING status. Review the notes. Show the saved rep approval for LD01085. Explain that it is a local business decision and does not change the TMS to BOOKED. |
| 3:50-4:40 | Show qa-results.md and native test results. Explain one blocked code-bypass attempt and one uncertainty/duplicate-send control. Separate live evidence from synthetic cases. |
| 4:40-5:00 | State the measured outcome and the important assumptions. Explain that external finalization is unresolved and outline the next production work. |

## Before pressing record

- Verify reviewer access, the exact repository commit and the active workflow.
- Use make warm only if the dashboard needs the service. The post-card runtime
  check passed. Both prototype booking permissions are consumed; do not place
  another booking or reuse LD01085/LD01094.
- Hide code entry and inbox content in the existing call recording. Redact the
  spoken code in the final audio, with a "verification code redacted" label.
  The underlying verification was an actual human action.
- Keep the App open and signed in. Ensure real and synthetic cohorts are clear.
- If any check fails, record the failure honestly and stop the booking attempt.
  A repeat take on another load needs another owner authorization.

## Evidence to use

The latest real run is 112f1a4a-84f3-420f-bce4-d7f374b381d1, load LD01085,
MC 138328, total 2950, TMS PENDING and reference EME8U26DKEX5DESS.
Local rep confirmation is saved. Its full speech assessment is in qa-results.md.
Use the separate no-send voice run only to demonstrate the repaired handoff.

The original LD01094 call is a failed-consent example and must never be
confirmed, resent or shown as a clean success. Neither spent load can be used
for another take. A new real submission would require separate exact-load
authorization, which is not part of this recording plan.
