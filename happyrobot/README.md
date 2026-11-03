# HappyRobot workflow

The voice workflow lives in the HappyRobot workspace: Inbound Carrier Sales, `01a18119-67a1-79a3-b220-369aa359d4fb`, with Version 2 (`ohsjtpsl4dl5`) live in production. This folder holds a reviewable copy of what matters in it. The workspace is the source of truth.

| File | Contents |
|---|---|
| [prompt.md](prompt.md) | The live prompt, the six tools and how they reach the service, and the Version 3 candidate change |
| [qa-evals.json](qa-evals.json) | The 19 conversation evals: each conversation, what it expects, and the mocks that keep every eval away from the live service |

Results are in [docs/qa-results.md](../docs/qa-results.md). The workflow itself is one web call trigger, one inbound voice agent with this prompt, and six tools, each a webhook to the service.
