# Five-minute walkthrough

The owner will handle recording and editing separately. The video is not part of
this run's remaining workflow gate. Use the exact final call identified in
PROTOTYPE_REPORT.md, followed by its App record and QA evidence. Do not present
two different calls as a single clean call.

| Time | Show and explain |
| --- | --- |
| 0:00-0:30 | The inbound carrier problem, the web-call entry and what the agent handles. |
| 0:30-3:00 | The final native call: active MC, fresh email verification, lane match, a real agent counteroffer, clearly accepted total, natural booking permission, full simulated-transfer disclosure and agent hangup. |
| 3:00-4:00 | That same run in Apps: MC, load, agreed rate, reference, actual PENDING status, redacted transcript and saved rep decision. Explain that rep approval is separate from external confirmation. |
| 4:00-4:40 | QA: verification bypass, unavailable load, leading-zero code, TMS faults and duplicate-send controls. Distinguish actual integrations from mocked cases. |
| 4:40-5:00 | The measured outcome, the unanswered external-finalization question and the next production work. |

## Recording controls

- Redact the verification code in screen and audio while keeping the sequence
  honest. Keep the private original out of the submitted package.
- Show only project windows. Keep inbox content, credentials, raw platform logs
  and internal pricing off screen.
- Use the same final run throughout. Preserve the earlier failed calls as QA
  history, not as substitute evidence of this run's spoken handoff.
- The final call's native recording is the voice source. Rep confirmation can
  be shown as the saved App decision if it was not recorded on screen.
- Never resend that load to recreate a shot. Another live take needs a fresh
  allocation and new owner authorization. Live mode stays off after the test.
- Verify final reviewer access, the selected commit and the video redaction
  before submission. No publication or external email is authorized here.

Links: [workflow](https://platform.happyrobot.ai/deployments/yhcdrf4kne4j),
[dashboard](https://carrier-sales-santiago.happyrobot.dev), [QA](qa-results.md).
