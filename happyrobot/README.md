# HappyRobot workflow

Inbound Carrier Sales lives in the HappyRobot workspace, workflow 01a18119-67a1-79a3-b220-369aa359d4fb. Version 3 (5j04ci46nsbf) is live. Version 4 (l8x9v2kyt4mc) is an unpublished candidate. The workspace is authoritative; these files make the important configuration and evidence reviewable.

| File | Contents |
|---|---|
| [prompt.md](prompt.md) | Live Version 3 prompt, opening line and six service tools |
| [prompt-v4.md](prompt-v4.md) | Exact unpublished Version 4 continuation candidate |
| [qa-evals.json](qa-evals.json) | Historical 22 checkpoint definitions and as-run fixtures, not current-contract fixtures |
| [e7-candidate.json](e7-candidate.json), [e7-results.json](e7-results.json) | Six current candidate checkpoints, locks and 18/18 results |
| [simulations.json](simulations.json) | Two fully mocked full-workflow text simulations, criteria, setup error and manual limits |

Results and failures are in [QA results](../docs/qa-results.md). The workflow has a web-call trigger, an inbound voice agent and six tools. Version 4 adds an end-report webhook after the agent, including calls with no earlier tool. This is not a guaranteed post-call summary or universal hangup capture. Publication requires owner approval after service deployment.
