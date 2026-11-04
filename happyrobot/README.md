# HappyRobot workflow

**Proposal checkout.** The [Friday pilot guide](../docs/proposal.md) identifies the branch changes, test evidence and deployment prerequisites. Hosted links and release descriptions below refer to the published baseline. The proposal voice candidate and App are separate from the published release.


The latest experimental source is the [Version 10 prompt](prompt-proposal-v10.md), [bindings](proposal-tool-bindings-v10.json) and [two complete mocked ending replays](qa-proposal-v10.json). Both replays ended promptly after the exact deal recap. This candidate is unpublished, with full regression and real voice acceptance still required. The Version 9 checkpoint score below does not apply to Version 10.

The [Version 9 prompt](prompt-proposal.md), [native tool bindings](proposal-tool-bindings.json) and [candidate QA results](qa-proposal.json) belong to the unpublished proposal. Its final checkpoints passed 71/73, including all fourteen new cases. The two original failed grades and the full-replay time invention and idle-timeout failures are retained. Version 9 is not accepted for promotion. See the [release gates](../docs/proposal-review.md#voice-candidate-evidence).

Current confirmation follow-up: the owner's Version 7 recording exposed a bypass after an explicit No. The narrow Version 8 fix is now live and passes 24/24 focused checks, 118/118 full-suite checkpoints and both mocked recording replays. Pricing is unchanged. See [the correction and its limits](../docs/confirmation-fix.md). The Version 7 acceptance wording below is historical and is superseded by this finding.

Inbound Carrier Sales lives in the HappyRobot workspace, workflow 01a18119-67a1-79a3-b220-369aa359d4fb. Version 8 (kvexhw5fzj4y) is live under the owner's existing release approval, replacing Version 7 (67nko7p112j2). The workspace is authoritative; these files make the important configuration and evidence reviewable. Eleven Version 6 calls now provide timed closing and stored end-event evidence. Historical Version 7 addressed amount intent and notes. The later recorded confirmation bypass is fixed in live Version 8; see [the tuning report](../docs/voice-tuning.md).

| File | Contents |
|---|---|
| [prompt.md](prompt.md) | Historical Version 3 prompt, opening line and six service tools |
| [prompt-v4.md](prompt-v4.md) | Historical Version 5 prompt, with its historical filename retained |
| [prompt-v8.md](prompt-v8.md) | Live Version 8, confirmation precedence and corrected-total readback |
| [qa-v8-confirmation-regression.json](qa-v8-confirmation-regression.json), [qa-v8-recording-replays.json](qa-v8-recording-replays.json) | 118/118 locked checkpoints, retained baseline failures and two complete mocked replays |
| [prompt-v7.md](prompt-v7.md) | Historical Version 7, conditional amount readback and complete operating notes |
| [qa-v7-amount-confirmation.json](qa-v7-amount-confirmation.json) | Exact draft, 51 checkpoints twice, all iterations and fixture corrections |
| [qa-v7-conversations.json](qa-v7-conversations.json) | Two fully mocked split-amount text traces, with closing limits |
| [qa-v6-owner-calls.json](qa-v6-owner-calls.json) | Eleven sanitized human transcripts and stored outcomes, four local holds |
| [prompt-v6.md](prompt-v6.md) | Historical Version 6 prompt; its time-display dependency is deployed in service release 17 |
| [qa-v6-audit-fixes.json](qa-v6-audit-fixes.json) | Historical Version 6 prompt SHA, revised time fixtures, 40 checkpoints twice, and closing follow-up evidence |
| [qa-voice-tuning.json](qa-voice-tuning.json) | Prior 40 checkpoint definitions/references, per-run grades, prompt iterations and retained corrections/failures through 18e26ba |
| [qa-voice-tuning-conversations.json](qa-voice-tuning-conversations.json) | Saved synthetic full-text traces, for offline argument/order/closing checks; not voice evidence |
| [qa-evals.json](qa-evals.json) | Historical 22 checkpoint definitions and as-run fixtures, not current-contract fixtures |
| [e7-candidate.json](e7-candidate.json), [e7-results.json](e7-results.json) | Six historical candidate checkpoints, locks and 18/18 results |
| [qa-v4-full.json](qa-v4-full.json), [qa-v4-results.json](qa-v4-results.json) | Historical full 22 suite, corrected contract fixtures, 66 pinned Version 4 runs: 58 pass, 8 fail, with failure observations |
| [simulations.json](simulations.json) | Two fully mocked full-workflow text simulations, criteria, setup error and manual limits |

Results and failures are in [QA results](../docs/qa-results.md). The workflow has a web-call trigger, an inbound voice agent, six tools and the end-report webhook introduced in Version 4. It has 16 nodes; the failed closing-module experiment is removed. This is not a guaranteed post-call summary or universal hangup capture. Version 6 followed the approved service deployment; Version 8 is a prompt-only publication. The owner reports a successful normal Version 8 call, not independently reviewed; the split-number edge case has mocked regression coverage but no new live speech retest. Checkpoints explicitly lock six external actions; full simulations lock seven, including call_ended. Never run tests with inherited live actions.
