# Voice workflow

The HappyRobot workflow that answers carrier calls. The workspace is the source of truth; these files make its configuration and test evidence reviewable.

| File | Contents |
| --- | --- |
| [prompt-v20.md](prompt-v20.md) | The live Production prompt, including the warning before quoting incomplete display times |
| [tool-bindings-v20.json](tool-bindings-v20.json) | Protected AI disclosure, authenticated service bindings, search schema and enabled Northstars |
| [qa-v20-checkpoints.json](qa-v20-checkpoints.json) | Original draft and final prompt text evaluations, raw failures and manual assessment |
| [qa-v20-voice.json](qa-v20-voice.json) | Actual diagnostic audio calls, sanitized transcripts, service records and native audits |
| [prompt-v19.md](prompt-v19.md), [tool-bindings-v19.json](tool-bindings-v19.json) | Retained rollback configuration |
| [qa-v19-checkpoints.json](qa-v19-checkpoints.json), [qa-v19-voice.json](qa-v19-voice.json) | Previous release evidence |
| [history/](history/README.md) | Earlier prompts and evaluations, Versions 3 to 18 |

**Workflow:** web-call trigger, then an inbound voice agent whose protected fixed opening identifies the AI and asks for the MC number. Its tools are `verify_carrier`, `send_code`, `verify_code`, `find_loads`, `negotiate` and `close_call`; an end-of-call webhook reports how the call ended. The service controls verification, prices and reservations. A prompt mistake cannot exceed the ceiling or send a booking.

**Links:** [workflow editor, Version 20](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w) · [Production web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc)

Version 20 was promoted after Development audio acceptance and independent review, then checked through the Production endpoint. Version 19 remains available for rollback. The demo service and populated Twin staging database are deliberately shared across workflow environments. Hosted booking sends remain off.

Scores and limitations are in [results](../docs/results.md). Text evaluations mock all external tools. Actual audio uses separate recorded evidence. Native audit grades are model judgments, with non-applicable criteria kept separate; Northstar prompt-span coverage is not a pass rate.
