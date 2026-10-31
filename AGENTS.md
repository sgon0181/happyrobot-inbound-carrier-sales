# Project context

`PROJECT_GUIDE.md` summarizes the assignment and relevant official documentation for this project. It is the starting reference for agents; source links are included for details. The local assignment PDF is the source of challenge requirements.

# Workflow

One agent writes at a time, and Codex reviews the result.

1. Only the agent assigned as writer changes tracked files for a task. Other agents stay read-only.
2. The writer makes one local commit on `main` and reports its SHA and validation.
3. Codex reviews that commit, and findings go back to the writer.
4. Nothing is pushed until the review is done and the owner approves the push.
