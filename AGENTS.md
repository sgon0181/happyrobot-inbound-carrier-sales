# Project context

`README.md` is the map of this repository. `ARCHITECTURE.md` explains how the system works, and `docs/decisions.md` records why, along with open checks. The assignment PDF in `docs/` is the source of challenge requirements, summarized in `docs/assignment.md`.

Read `docs/onboarding.md` for access setup, current state and platform resources. For TMS work, read `docs/tms/README.md` before implementing or testing the integration, then `docs/tms-contract.md` for sanitized observations, fixtures and blocked/protected inventory. These tracked references are shared by Codex and Claude Code; ignored local packets are optional evidence, not required onboarding.

Production code lives in `service/` on `main`. Branch `prototype/e2e` is reference only: port from it deliberately, one reviewed piece at a time, and never merge it. Meet the engineering gates in `ARCHITECTURE.md` section 14, and report the production line count in each commit.

# Writing

Never output Unicode U+2014, U+2013, or other long dash punctuation in responses or generated content. Use commas, periods, colons, semicolons or parentheses instead. Ordinary ASCII hyphens are allowed in compound words, code and bullet lists; double hyphens are not sentence punctuation. Paraphrase prohibited characters in source material, and check output before delivery.

# Workflow

One agent writes at a time, and Codex reviews the result.

1. Only the agent assigned as writer changes tracked files for a task. Other agents stay read-only.
2. The writer makes one local commit on `main` and reports its SHA and validation.
3. Codex reviews that commit, and findings go back to the writer.
4. Nothing is pushed until the review is done and the owner approves the push.
