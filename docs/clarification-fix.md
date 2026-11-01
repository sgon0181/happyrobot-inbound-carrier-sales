# Price clarification and call ending, 2026-11-01

The second owner call, run 043af7ce-ecb6-42f8-b8f4-162143ce9d20 on prototype
v7, passed FMCSA and the new Gmail SMTP code. It found LD01085 and handled two
actual price increases. It sent no booking.

The agent treated an incomplete offer question as price acceptance. Later, the
caller asked "What's the rate". The agent answered, declared that permission
was unconfirmed, and ended the call. All three preparation responses were
confirmation_required without end_call_required. Native agent_hung_up proves
the agent ended it. The consent guard correctly withheld the TMS submission.

The two genuine counters were not backend confirmation defects. No evidence
from this call supports blaming identical-price agreement resets. The error
was the agent's interpretation and premature closing.

## Change

- Give the total first, then a short operational summary. Retain material
  pickup, delivery and notes, with other cargo details available on request.
- Distinguish a rate question from acceptance or a counter. "Is that 2900?"
  asks for information; "Can you do 2900?" proposes a counter.
- Wait for incomplete speech. Never ask a clarification question while also
  submitting an assumed answer through a tool.
- Answer a rate question with the current total and wait. Pending permission
  is not a refusal, booking failure or reason to hang up.
- Read the canonical booking question alone, without a preface. A new booking
  intent after a rate-only answer may require that standalone question again.
  A fresh yes to it goes directly to request_booking without renegotiation.
- Default close classification is ended_without_booking. Existing business
  outcomes are preserved. End initiator requires separate trusted evidence.
  The observed v7 call was annotated with its native agent-end evidence.

The consent matcher, authority/code gates, pricing ceiling, counter budget,
claiming, one-shot send and live authorization remain intact. Main and the
original workflow were not changed.

## Verification

154 offline service tests passed. Three native text regressions used eight
skip mocks each. They passed manual review and native grades:

| Case | Observed behavior |
| --- | --- |
| Incomplete offer question | Asked for completion, repeated the price, no agreement or booking action; ended only after caller explicitly declined |
| Rate clarification and one counter | Exactly one genuine counter, standalone permission preparation, rate-only answer and waiting; no premature close |
| TMS outage | Correct spoken refusal, finish_call and native hangup. Native target completed; outer wrapper alone hit its backstop |

The hybrid test executed only the real request_booking HTTP action; seven
other HTTP actions were skipped. A fresh Development E2E run was atomically
seeded as synthetic with a fake load and explicitly simulated verification.
Its actual responses were confirmation_required, confirmation_required, then
consent_verified with booking_submitted:false. The renewed question and fresh
yes matched the saved session, message IDs and agreement version. Exactly one
negotiation occurred. Closing speech and native hangup completed. Manual
inspection, grade and outer wrapper passed.

Zero booking rows were created. Every prior write-intent ID and the real
LD01085 authorization were unchanged. The synthetic test call was closed
afterwards. This proves the deployed permission path, not a human voice
booking or a new TMS receipt.

One earlier hybrid fixture attempt failed before seeding. The real service
returned carrier_ineligible and closed safely. Its failed result is retained.
An invalid immediate run-status assertion was corrected to the documented
not_started, scheduled and running values. An earlier no-run preflight also
found that the API omits an explicit inherit override on readback. Those setup
failures are separate from the successful corrected test.

Tested Development v8 was promoted through an executable-equivalent v9 fork.
Eighteen nodes and seven safe output schemas were checked before Production
publication. The later real v9 owner call passed fresh consent and sent the
allocated LD01085 request at 2950, receiving PENDING. Its permission is now
consumed. The shortened spoken handoff on that call was a separate defect,
addressed with a fixed literal tool and no-send voice check. See
[the latest audit](prototype-evidence/v9-real-call-audit.json).

## Evidence

- [Owner-call failure](prototype-evidence/owner-v7-clarification-failure.json)
- [Evidence-based annotation](prototype-evidence/owner-v7-review-annotation.json)
- [Three dialogue regressions](prototype-evidence/v8-dialogue-regressions.json)
- [Failed hybrid setup](prototype-evidence/v8-hybrid-setup-failure.json)
- [Corrected hybrid permission proof](prototype-evidence/v8-hybrid-consent.json)
- [v8-to-v9 parity](prototype-evidence/workflow-v8-v9-parity.json)
- [Pre-call allocation check](prototype-evidence/v9-pre-call-check.json)
