# Recorded-call confirmation release

Version 8 (`kvexhw5fzj4y`, ID `01a1a4f6-79a3-7c40-8732-589b3adfdcfd`) replaced Version 7 in production on 2026-11-04 at about 05:21 UTC. The owner had approved non-portal release work and then instructed the narrow confirmation fix. Independent read-only review passed implementation commit `eaa2661a6671dbea3421fb03fa1d7933ce5d3ae9` before publication. Post-publication reads returned published/live true and exact root and negotiate function equality with the tested draft.

Root SHA-256: `53a884aea629114fa6d3342b9c8cf9f392bf376ca053622ab1f561821d33437c`. [Exact source](../../../../happyrobot/history/prompt-v8.md), [regression evidence](../../../../happyrobot/history/qa-v8-confirmation-regression.json), [both full mocked replays](../../../../happyrobot/history/qa-v8-recording-replays.json), [fix and limits](../../confirmation-fix.md). The QA manifest is retained as the as-tested draft snapshot; this record supersedes its publication status, without rewriting results.

Validation: final focused 24/24, frozen full checkpoint suite 118/118, both full text replays submitted exactly 1125 only after corrected readback and explicit affirmation. Baseline failures and the unsuccessful first revision remain retained. These are text/model and tool-sequence checks, not proof of audio recognition or physical voice timing. The text replays lack a recorded spoken farewell, so no new complete voice-closing pass is claimed.

Service release 17, App Build 20, pricing, model, opening and 16-node graph are unchanged. The authenticated service snapshot at 05:21:22 UTC returned 200 and live_booking false. No secret, cohort flag, reservation or booking was changed; no LOAD_BOOK or submission portal action occurred. Production code remains 2919 Python and 4613 App TypeScript/TSX physical lines. make check passes 487 tests, strict types and lint, actual 100% service statements/branches, Radon maximum 10 (B), module 287 and function 48.

## Submission package consistency

A later owner screenshot exposed a stale Version 7 claim in the build-description PDF. The live workflow remained Version 8. Current documentation, the PDF and local source ZIP are refreshed together; the source ZIP uses reviewed tracked files only, and the local package manifest records its commit and hashes. Historical release/QA artifacts retain their original versions. The owner reports a successful normal Version 8 call, without independent transcript/audio review of that latest call. This refresh does not contact the submission portal or send a booking.
