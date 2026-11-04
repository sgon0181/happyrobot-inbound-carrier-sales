# Voice tuning after the owner's Version 5 calls

Status: local candidate, not released or accepted. Version 5 remains live. Version 6 (`alj9n98f66df`) is an unpublished draft. Closing is still an acceptance blocker: the text simulator does not reliably retain a spoken handoff or farewell, and no Version 6 human voice evidence was collected in this work. Do not interpret checkpoint passes as completion.

## What triggered the changes

Ten owner Version 5 transcripts and tool traces were reviewed, with one Version 4 comparison. Audio was not reviewed. No booking was sent during review or this build.

| Finding | Evidence | Candidate change |
|---|---|---|
| Incomplete dollar amounts became agreements | `8c48df03`: "1600 and 25" became 1600; caller later clarified 1625. `bdfb3886`: "6300 and 25 dollars" became 6300 | Ask for one complete total and wait before any tool. Relative additions and percentages also require an explicit total. Normal number words containing "and" remain valid. Reinforce the same rule in negotiate's rate parameter description |
| A counter was described as final | `f00eaae5`: counter 2050, round 1, became a spoken final offer on a best-price question | Final wording requires final_offer for this load and amount. Best-price questions can repeat the current offer, without inventing final status |
| Identical asks sounded like new offers | `4ac79d3a`: repeated 2200 asks returned the same 1775, round 2 | State that the offer remains unchanged and ask one yes/no question about accepting that amount. Keep D-26, fresh bounds and the round budget unchanged |
| Farewells reopened or did not end promptly | `8c48df03` and `36b0c336`; later text simulations also exposed idle endings | After recording close, use voice _hangup with closing words in _message. This requests speech and hangup in one action. Physical voice behavior is unverified |
| Pickup clocks lacked a timezone | Several pitches read UTC clock values without naming the zone | Service supplies pickup_time_display and delivery_time_display in America/Chicago, including CST/CDT and date rollover. Retain original ISO values and the unconfirmed source-UTC assumption |
| Unclear equipment reached search | "Drive in" produced invalid_search | Ask whether the caller means dry van and retain the lane while waiting. No speech engine, model, voice or transcription setting was changed |

## Evidence and boundaries

- Service commit `f2b0e9b`: six time-display regressions first failed, then passed. 457 offline tests, actual 100% over 1647 statements and 406 branches; gated business branches 256/256. Runtime Python: 2914 physical lines. ZoneInfo availability was checked in an offline python:3.12-slim container.
- This candidate adds an offline trace checker and 26 tests covering correct fixtures and corrupted amounts, clarification order, load, time, handoff, closing, reopening and ending. The combined make check result is 483 passing tests with the same actual service coverage. Runtime Python remains 2914 physical lines; the separate offline checker is 182 lines. The largest runtime module is 287 lines, largest function 48 lines and maximum Radon complexity 10 (B); the checker maximum is 8 (B). The offline checker is not a model or integration test.
- Current root prompt: `80a3b9fa0718c8b4bbb2541bb5e5ea9503af246eedf7559f3c876296fb823cb5`. [Exact text](../happyrobot/prompt-v6.md). Model and opening line remain unchanged. The negotiate description is the only retained tool-definition change.
- Current-contract checkpoints: 40 definitions, twice each, 80/80 native model grades. All six external actions were explicitly locked to literal outputs and read back. Twenty-two historical definitions are unchanged; S5 has a current-contract copy. The 17 new cases include separate text-only closing checks. Original definitions and failures remain retained.
- Full text simulations lock all seven external actions, including call_ended. They use constant outputs, not stateful backend validation. Actual arguments, conversation order and endings are recorded separately. They must not be counted as human calls or added to unit test counts.
- Earlier prompt iterations and fixture/scoring corrections are retained in [the manifest](../happyrobot/qa-voice-tuning.json). Corrections include a delivery-before-pickup fixture, omitted counter history, contradictory expected tool lists, an incorrect expected S5 rate, and a judge requiring a real transfer despite the assignment's spoken mock. One judge passed despite a mismatched expected rate. Native grades alone are insufficient evidence.
- A native prompt module after close_call was tested and removed. The refusal reached idle_timeout; its tool result also had an empty module-change ID. It did not establish reliable closing. The draft is back to the original 16-node shape, with no additional external action.

Saved full conversation traces are in [the replay file](../happyrobot/qa-voice-tuning-conversations.json), with other run IDs and observations in the manifest. It retains 410 checkpoint results across prompt iterations, including the final 80; these are not 410 different scenarios. Synthetic code fields are redacted and long dash punctuation is paraphrased. The checker deliberately reports missing speech or ending evidence; a nonzero exit must not be hidden or reclassified as a pass. The extra incomplete attempt's native [backstop screenshot](evidence/voice-v6/simulation-backstop.jpg) shows its N/A outcome and locked actions.

```bash
PATH="$PWD/.venv/bin:$PATH" make check
.venv/bin/radon cc service tools -n C -e 'service/tests/*' -s
.venv/bin/python tools/check_voice_tuning.py happyrobot/qa-voice-tuning-conversations.json
```

The text simulator uses hr_builtin_tool__end_conversation, while the real voice traces use _hangup with _message. Absence of a farewell in a text ending does not prove that the voice tool will omit it, but it does prevent claiming spoken closing is verified. Some simulations also stalled before reaching the intended scenario. Their cause was not established. Those executions are retained as incomplete, not successful calls.

## Review and acceptance order

**Strict full-text replay: 0/6 pass, exit code 1.** These saved traces use the preceding `c64020501010cba986811ce2a7557beb3828638d80f73b5e7f59dcd48a684cc4` root, which has the same closing mechanism. One conversation reached idle_timeout before negotiation, four have no recorded final farewell, and one waits for a caller reply after goodbye. An extra compound-amount attempt exceeded the simulator's internal three-minute backstop and has no retrievable workflow run. All are retained. The final `80a3b9fa` root changes the unchanged-offer acceptance question and adds V17; its exact checkpoint result is 80/80, not a full-conversation or voice pass.

| Saved full-text scenario | Amount or offer evidence | Strict closing check |
|---|---|---|
| Compound amount, repetition 1 | Negotiation not reached; idle timeout after the MC stage | Fail |
| Compound amount, repetition 2 | Clarification precedes negotiate at exactly 1625 | No recorded final farewell |
| Repeated ask, repetitions 1 and 2 | All repeated asks stay 2200; service offer stays 1775, accurately described as unchanged | No recorded final farewell |
| Ineligible refusal, repetition 1 | No matching or negotiation; close and ending tool recorded | No recorded final farewell |
| Ineligible refusal, repetition 2 | Refusal, close, farewell and ending tool recorded | Caller turn occurs between farewell and ending |

The checker is deliberately conservative and limited to the fixed simulation scripts. It accepts only reviewed clarification requests; unseen wording requires manual review. It does not understand arbitrary natural language or certify production conversations. Its 26 unit tests include the false passes found in independent read-only review. Fixing its caller-turn check changed the earlier 1/6 replay score to 0/6; that earlier apparent pass is not retained as a success.

1. Review the local service and voice/QA commits. No push, deployment, publication or secret change is included in this work.
2. After owner approval, push and deploy the service before publishing Version 6, because the prompt depends on its display fields. Keep booking sends off and calls synthetic for QA.
3. Run supervised voice checks: both compound amounts; an ordinary complete amount containing "and"; a percentage or relative addition; repeated asks including "or nothing"; successful handoff; ineligible refusal; and caller interruption/correction. Exercise agreement and refusal endings more than once.
4. Inspect the actual voice tool arguments and audio. Require no negotiate before clarification, exact agreed totals, no invented final status, unchanged repeats described truthfully, correct named times, and a final handoff or refusal followed by farewell and prompt hangup with no reopening question.
5. Read back the saved call and reservation records. A reservation is not final TMS booking. Keep all failed checks and reruns. Closing remains open until this voice evidence passes; do not call the submission candidate finished before then.

The cost of the amount rule is an extra turn for additions such as "a hundred more." D-26 still conflates identical spoken asks with request retries because there is no stable operation ID; this change improves wording without weakening retry protection. Central Time is a display policy, not validation of the TMS's source timezone.
