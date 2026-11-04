# HappyRobot workflow

Inbound Carrier Sales lives in the HappyRobot workspace, workflow 01a18119-67a1-79a3-b220-369aa359d4fb. Version 6 (alj9n98f66df) is live after owner-approved release, replacing Version 5 (zad4fuknryd8). The workspace is authoritative; these files make the important configuration and evidence reviewable. Closing remains a voice acceptance blocker; see [the tuning report](../docs/voice-tuning.md).

| File | Contents |
|---|---|
| [prompt.md](prompt.md) | Historical Version 3 prompt, opening line and six service tools |
| [prompt-v4.md](prompt-v4.md) | Historical Version 5 prompt, with its historical filename retained |
| [prompt-v6.md](prompt-v6.md) | Live Version 6 prompt; its time-display dependency is deployed in service release 17 |
| [qa-v6-audit-fixes.json](qa-v6-audit-fixes.json) | Current Version 6 prompt SHA, revised time fixtures, 40 checkpoints twice, and closing follow-up evidence |
| [qa-voice-tuning.json](qa-voice-tuning.json) | Prior 40 checkpoint definitions/references, per-run grades, prompt iterations and retained corrections/failures through 18e26ba |
| [qa-voice-tuning-conversations.json](qa-voice-tuning-conversations.json) | Saved synthetic full-text traces, for offline argument/order/closing checks; not voice evidence |
| [qa-evals.json](qa-evals.json) | Historical 22 checkpoint definitions and as-run fixtures, not current-contract fixtures |
| [e7-candidate.json](e7-candidate.json), [e7-results.json](e7-results.json) | Six current candidate checkpoints, locks and 18/18 results |
| [qa-v4-full.json](qa-v4-full.json), [qa-v4-results.json](qa-v4-results.json) | Current full 22 suite, corrected contract fixtures, 66 pinned Version 4 runs: 58 pass, 8 fail, with failure observations |
| [simulations.json](simulations.json) | Two fully mocked full-workflow text simulations, criteria, setup error and manual limits |

Results and failures are in [QA results](../docs/qa-results.md). The workflow has a web-call trigger, an inbound voice agent, six tools and the end-report webhook introduced in Version 4. It has 16 nodes; the failed closing-module experiment is removed. This is not a guaranteed post-call summary or universal hangup capture. Version 6 was published after the approved service deployment; current-version voice acceptance remains open. Checkpoints explicitly lock six external actions; full simulations lock seven, including call_ended. Never run tests with inherited live actions.
