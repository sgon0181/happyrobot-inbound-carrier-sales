# Project context

`PROJECT_GUIDE.md` summarizes the assignment and relevant official documentation for this project. It is the starting reference for agents; source links are included for details. The local assignment PDF is the source of challenge requirements.

For TMS work, read `docs/tms/README.md` before implementing or testing the integration. It is the shared operating reference for Codex and Claude Code. `docs/tms-contract.md` records observed behavior and its limits; `ARCHITECTURE.md` records design decisions. Check the reference's newer booking-status caveat before relying on the architecture's booking sequence.

# Writing

Never output Unicode U+2014, U+2013, or other long dash punctuation in responses or generated content. Use commas, periods, colons, semicolons or parentheses instead. Ordinary ASCII hyphens are allowed in compound words, code and bullet lists; double hyphens are not sentence punctuation. Paraphrase prohibited characters in source material, and check output before delivery.

# Workflow

One agent writes at a time, and Codex reviews the result.

1. Only the agent assigned as writer changes tracked files for a task. Other agents stay read-only.
2. The writer makes one local commit on `main` and reports its SHA and validation.
3. Codex reviews that commit, and findings go back to the writer.
4. Nothing is pushed until the review is done and the owner approves the push.
