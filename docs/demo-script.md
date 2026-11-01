# Five-minute business walkthrough

Recording readiness: pending the clean consented call and real App review.
Use actual completed evidence. Do not present a simulation as a real booking.

| Time | Show and say |
| --- | --- |
| 0:00-0:30 | Explain missed calls, repeated verification and inconsistent negotiation. Show the web-call entry and describe the first leg the agent owns. |
| 0:30-2:50 | Make the real call: active MC, new emailed code, matching lane, one counter, exact total, explicit permission, neutral senior review and spoken mocked transfer. Let the agent hang up. Never show the inbox code or credential screens in the final recording. |
| 2:50-3:50 | Open the real call in Apps. Show load, MC, agreed rate, receipt and actual PENDING status. Review the notes. Record rep approval only for the clean call. Explain that it is a local business decision and does not change the TMS to BOOKED. |
| 3:50-4:40 | Show qa-results.md and native test results. Explain one blocked code-bypass attempt and one uncertainty/duplicate-send control. Separate live evidence from synthetic cases. |
| 4:40-5:00 | State the measured outcome and the important assumptions. Explain that external finalization is unresolved and outline the next production work. |

## Before pressing record

- Verify reviewer access, the exact repository commit and the active workflow.
- Check Fly is outside trial limits, the service is healthy and the one-shot
  load authorization is for fresh inventory. Existing spent loads stay blocked.
- Verify the new SMTP email arrives after the call begins. Hide code entry and
  inbox content in the shared recording. Redact the spoken code in the final
  audio too, with a clear "verification code redacted" label. The underlying
  verification remains an actual human action, not a simulated replacement.
- Keep the App open and signed in. Ensure real and synthetic cohorts are clear.
- If any check fails, record the failure honestly and stop the booking attempt.
  A repeat take on another load needs another owner authorization.

## Owner call instructions

The exact lane and disposable load will be selected immediately before the
call. Give MC 138328. Ask for 25 more than the opening offer, then accept the
returned rate. First clarify the total without authorizing a booking. The
agent must wait and ask the exact permission question again. Only then say
"Yes, please book it." Wait for the mocked transfer and agent hang-up.

The original LD01094 call is a failed-consent example and must never be
confirmed, resent or shown as a clean success.
