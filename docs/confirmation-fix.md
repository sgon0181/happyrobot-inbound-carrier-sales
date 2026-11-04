# Recorded-call confirmation fix

The owner's Version 7 call `b61fba6e-0eaf-4c80-8df1-45968561f3b7` reproduced a voice-flow defect. After reading back 110025, the agent treated "No. It is 110025 dollars" as permission to negotiate. Later, "Yeah, 1125" supplied an amount after clarification but also reached negotiate before readback. The service countered at its own approved amounts, never agreed, and created no reservation. Pricing was working; confirmation was not.

[Sanitized source transcript and Twin state](../happyrobot/qa-v7-recorded-confirmation-failure.json) retain the failure. Audio was not listened to. The platform transcription concatenated the intended 1125 into 110025; this fix does not change speech recognition or guess the caller's intended sum.

## Narrow change

Version 8 is an editable copy of Version 7. Only root step 5 and the negotiate rate description change. The pending-confirmation gate now comes before direct-submission rules. No plus unchanged digits cannot confirm. A different complete total is a correction, including "Yes, I mean 1125", and needs a fresh readback and affirmative. "Yeah, 1125" after a clarification question supplies a proposed total. Ordinary initial amounts, direct acceptance, answered repeats and same-number service retries retain their behavior.

The service, pricing, model, opening, workflow graph and App are unchanged. No portal action, booking, secret change or service deployment is part of this fix. The source is [prompt-v8.md](../happyrobot/prompt-v8.md), root SHA-256 `53a884aea629114fa6d3342b9c8cf9f392bf376ca053622ab1f561821d33437c`.

## Verification

[Checkpoint evidence](../happyrobot/qa-v8-confirmation-regression.json) pins definitions, literal mocks, every run and both prompt iterations. Eight recording-derived cases ran three times on unchanged Version 7: 16/24 passed, 8 failed. The first draft scored 18/24 and remains retained. Final focused revision: 24/24. The frozen final root and tool then passed 59 current scenarios twice: 118/118. All six external tool actions were explicitly locked to literal outputs and read back before testing.

The new cases cover negative same-digit responses, a newly clarified 1125, corrected totals, repeat requests, Yes with changed digits, confirmed corrected amounts, ordinary initial amounts and an explicitly confirmed extreme ask. The last case preserves service pricing authority rather than imposing a new voice-side rate policy. These are native model grades, not audio or backend integration proofs.

`PATH="$PWD/.venv/bin:$PATH" make check` passes 487 offline tests, ruff/format and strict mypy. Actual service coverage remains 1650/1650 statements and 406/406 branches; business branches 256/256. Radon maximum 10 (B), maximum module 287 and function 48 physical lines. Production code remains 2919 Python and 4613 App TypeScript/TSX physical lines.

Two fully mocked multi-turn replays completed in 59 seconds each. Both withheld negotiation through the repeated 110025 readback and the explicit No. They read back the corrected 1125 and made exactly one negotiate call at 1125 after a fresh affirmative. All seven external actions, including the end callback, were locked and read back. Both called close_call and the text ending tool after the caller declined. No spoken farewell is recorded, so no complete voice closing pass is claimed. After No plus unchanged digits they repeated the readback rather than asking an open total question; the confirmation gate remained pending. [Saved arguments and sequences](../happyrobot/qa-v8-recording-replays.json) preserve this limitation.

The implementation commit captured the verified draft. It was then independently reviewed and published under the owner's existing non-portal release approval. [Publication readback](releases/2026-11-04-v8/README.md) confirms the exact live root and tool. No new owner call is required to run these regressions. Audio recognition and physical voice timing remain outside the mocked checks.

[Native regression screenshot](evidence/voice-v8/recording-regression.png) shows the final R1 continuation asking for a complete total without a new tool call. Independent read-only review reconciled all result counts, mock locks, prompt/tool consistency and both replay sequences.
