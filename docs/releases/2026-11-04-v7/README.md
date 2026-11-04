# Version 7 release

The owner approved publication of the reviewed fix in `9d7a149`. Version 7 (`67nko7p112j2`) replaced Version 6 in production on 2026-11-04. Post-publication reads verify the exact root and negotiate schema. Root SHA-256: `91887bf1ecd2710d07446318f80d144eea55c1aec139cf23c0a812b60720b07b`.

Service release 17 and App Build 20 were not redeployed. Booking sends remain off and calls remain synthetic. No secret changed and no booking was sent. [Release facts](release.json) and [the exact prompt](../../../happyrobot/prompt-v7.md) identify the source. The as-tested checkpoint artifact remains a historical draft snapshot, not a claim that Version 7 is still unpublished.

Validation: 487 service tests, actual 100% statements/branches, strict types/lint and Radon B or better; 51 checkpoints twice, 102/102. Two fully mocked text traces preserve the corrected 3825 amount and full notes but lack recorded final spoken closing. The earlier 11 Version 6 human-call traces provide proactive closing and stored end-report evidence. All failures and limits remain in the QA report. Production code is unchanged: 2919 Python lines and 4613 App TypeScript/TSX lines.

One focused Version 7 human call remains. Use the single-call script in [the owner checklist](../../final-owner-checklist.md); do not repeat the successful Version 6 suite. The owner video and reviewer-account access remain open. Luke's latest challenge thread has no new response on Q8 or reviewer accounts. A source ZIP will accompany the private repository link in the portal; no unknown account is granted access.
