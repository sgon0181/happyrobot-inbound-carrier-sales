# Conversation coverage, candidate run

The actual second owner rehearsal exposed a language-to-tool error: the transcript
contained "3600 and 25", but the agent first submitted 3600. The service applied its
policy correctly to that incomplete amount. The caller corrected it before giving
booking permission. No booking was sent in either rehearsal.

The revised prompt clarifies shorthand totals, keeps increments and corrections,
waits for unfinished amounts, and distinguishes price agreement from permission.
The final prompt uses full monetary wording outside the exact booking question.
A neutral trailing "One moment" no longer obstructs an otherwise valid consent
proof. That backend correction retains question, answer and ignored-message IDs.
All original rejection tests remain passing.

## Observed language cases

All 17 native conversation cases used all nine HTTP skip mocks, verified before
launch and in each actual run snapshot. Every submitted rate matched its expected
amount. This is model/tool-boundary evidence, not real business submission.

| Input or situation | Observed behavior |
| --- | --- |
| "Okay, lets do 3600 and 25" | Clarified 3625, waited for the price answer, submitted 3625. |
| Add 25 to the current 3600 | Clarified 3625, waited, submitted 3625. |
| Full words for3625 | Submitted 3625 and read the total before booking permission. A complete clear total does not need an extra price-confirmation loop. |
| Explicit3625 total | Submitted 3625. |
| Twenty percent more | The conversational simulator substituted4320. Exact deterministic checkpoints separately proved the actual percentage input and 4320 calculation. |
| Rate/final-price information questions | Repeated the current offer without negotiating or preparing a booking. |
| Price acceptance only if pickup moves | No agreement or booking preparation; did not promise a schedule change. |
| Booking answer conditional on driver assist | No advancement beyond the existing permission preparation. |
| Hesitation and changed mind | No advancement beyond preparation. |
| "Sure, thanks" after exact question | Called the permission tool directly without renegotiating. Actual approval is checked separately by the backend. |
| Withdrawal and goodbye | No permission call after withdrawal; honored stop. |
| "Could you" followed by "repeat the rate" | No negotiation or booking preparation. |
| "No, I mean 3625 total" | Treated as a price correction, not a refusal to continue. |
| 3700 corrected to 3725 within one turn | Read back3725, waited, submitted 3725 once. |
| "Is that3600 or3625?" | Repeated the actual 3600 offer without a tool. |
| Numeric phrase split before the 25 | Preserved the 25 and submitted 3625. v16 prematurely suggested3600; final v17 exact checkpoint waited for completion instead. |
| "Yeah. That sounds about right" after booking question | Did not treat price-only affirmation as permission; asked for explicit permission again. |

These quoted phrases are synthetic fixture descriptions. Read the
[17-case evidence](prototype-evidence/candidate-v16-conversation-matrix.json)
for exact run IDs, tool counts, grades and partial-run boundaries.

## Exact message checkpoints

A separate test feeds exact conversation messages into the same native prompt,
without a simulator rewriting the caller. Its service key is explicitly replaced
with an invalid sentinel. Any HTTP tool is rejected before business logic, and
no dummy-call row is created. These are HYBRID model checkpoints, not integration
success. On final v17:

- An unfinished amount prompted the caller to finish, with no partial guess/tool.
- The completed fragment prompted clarification of 3625, with no tool yet.
- "Okay, so3600 is the offer?" remained a question, with no tool.
- Twenty percent more prompted4320 total and waited.
- Confirming that proposed total selected agree_rate with 4320 exactly. The
  deliberate authentication denial prevented further business execution.

[Exact checkpoint evidence](prototype-evidence/candidate-v17-exact-checkpoints.json)
keeps the actual output and arguments. A baseline custom-eval setup compared only
tool names because the optional argument shape was not retained. Its passed grade
was discarded; the actual wrong3600 argument remains failed evidence.

## Consent and closure limits

Static confirmation_required mocks cannot prove a required-to-approved state
transition. Offline tests exercise the actual finite consent matcher, exact
question, anchor, session, interruption, amount and negation checks. The real
rehearsals independently passed native consent with zero intents or sends.
The completed final owner run, if passed, is identified in PROTOTYPE_REPORT.md.

Some simulated cases reached a harness backstop after proving their language
phase. Do not claim full closure for those traces. v17 standard QA also found
one genuine ineligible-call closing failure: the agent refused correctly, spoke
a goodbye, omitted the closing tools, and idled about 66 seconds before closure.
No load, rate or booking followed. This remains a quality issue for review.

Uncertainty's fixed handoff can be assessed as presentation only: its static
senior_review mock omits the real permission transition. Failed consent/counter
grades on that fixture are preserved. Grades never replace inspected tool
arguments, actual native ending, stored business facts or a real receipt.

Text tests do not prove pronunciation, acoustic interruption behavior or reliable
handling of every possible utterance. The live final call is the integration
proof; the owner will handle the video separately.

[Read-only terminal capability review](prototype-evidence/candidate-terminal-capability-review.json)
found a model-selected built-in hangup and global timeouts, but no verified
per-outcome automatic hangup action. No unsupported flag was added.
