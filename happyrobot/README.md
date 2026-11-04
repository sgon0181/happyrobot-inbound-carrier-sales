# HappyRobot workflow

Inbound Carrier Sales lives in the HappyRobot workspace, workflow 01a18119-67a1-79a3-b220-369aa359d4fb. Version 7 (67nko7p112j2) is live after owner-approved publication, replacing Version 6 (alj9n98f66df). The workspace is authoritative; these files make the important configuration and evidence reviewable. Eleven Version 6 calls now provide timed closing and stored end-event evidence. A remaining amount-intent failure and omitted notes are addressed in live Version 7; see [the tuning report](../docs/voice-tuning.md).

| File | Contents |
|---|---|
| [prompt.md](prompt.md) | Historical Version 3 prompt, opening line and six service tools |
| [prompt-v4.md](prompt-v4.md) | Historical Version 5 prompt, with its historical filename retained |
| [prompt-v7.md](prompt-v7.md) | Live Version 7, conditional amount readback and complete operating notes |
| [qa-v7-amount-confirmation.json](qa-v7-amount-confirmation.json) | Exact draft, 51 checkpoints twice, all iterations and fixture corrections |
| [qa-v7-conversations.json](qa-v7-conversations.json) | Two fully mocked split-amount text traces, with closing limits |
| [qa-v6-owner-calls.json](qa-v6-owner-calls.json) | Eleven sanitized human transcripts and stored outcomes, four local holds |
| [prompt-v6.md](prompt-v6.md) | Historical Version 6 prompt; its time-display dependency is deployed in service release 17 |
| [qa-v6-audit-fixes.json](qa-v6-audit-fixes.json) | Historical Version 6 prompt SHA, revised time fixtures, 40 checkpoints twice, and closing follow-up evidence |
| [qa-voice-tuning.json](qa-voice-tuning.json) | Prior 40 checkpoint definitions/references, per-run grades, prompt iterations and retained corrections/failures through 18e26ba |
| [qa-voice-tuning-conversations.json](qa-voice-tuning-conversations.json) | Saved synthetic full-text traces, for offline argument/order/closing checks; not voice evidence |
| [qa-evals.json](qa-evals.json) | Historical 22 checkpoint definitions and as-run fixtures, not current-contract fixtures |
| [e7-candidate.json](e7-candidate.json), [e7-results.json](e7-results.json) | Six current candidate checkpoints, locks and 18/18 results |
| [qa-v4-full.json](qa-v4-full.json), [qa-v4-results.json](qa-v4-results.json) | Current full 22 suite, corrected contract fixtures, 66 pinned Version 4 runs: 58 pass, 8 fail, with failure observations |
| [simulations.json](simulations.json) | Two fully mocked full-workflow text simulations, criteria, setup error and manual limits |

Results and failures are in [QA results](../docs/qa-results.md). The workflow has a web-call trigger, an inbound voice agent, six tools and the end-report webhook introduced in Version 4. It has 16 nodes; the failed closing-module experiment is removed. This is not a guaranteed post-call summary or universal hangup capture. Version 6 followed the approved service deployment; Version 7 is a prompt-only publication and needs one focused voice acceptance call. Checkpoints explicitly lock six external actions; full simulations lock seven, including call_ended. Never run tests with inherited live actions.
