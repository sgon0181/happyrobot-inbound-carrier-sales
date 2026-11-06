# Voice workflow

The HappyRobot workflow that answers carrier calls. The workspace is the source of truth; these files make its configuration and test evidence reviewable.

| File | Contents |
| --- | --- |
| [prompt-v19.md](prompt-v19.md) | The live prompt (Version 19, Production) |
| [tool-bindings-v19.json](tool-bindings-v19.json) | The fixed AI-disclosure opening and seven authenticated HTTP calls to the service: six agent tools and the end-of-call report |
| [qa-v19-checkpoints.json](qa-v19-checkpoints.json) | Platform text evaluations: definitions, raw grades, failures and manual review |
| [qa-v19-voice.json](qa-v19-voice.json) | Real web calls with generated callers, sanitized transcripts and outcomes |
| [history/](history/README.md) | Earlier prompts and evaluations, Versions 3 to 18 |

**Workflow:** web-call trigger, then an inbound voice agent whose fixed first message says it is an AI and asks for the MC number. Its tools are `verify_carrier`, `send_code`, `verify_code`, `find_loads`, `negotiate` and `close_call`; an end-of-call webhook reports how the call ended. The prompt only governs the conversation. Prices, verification and reservations are decided by the service, so a prompt mistake cannot exceed the ceiling or send a booking.

**Links:** [workflow editor, Version 19](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/l6zo75s4s4vk) · [web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc)

Scores are summarized in [results](../docs/results.md). Never run platform tests with live actions inherited from the workflow; evaluations mock all external tools.
