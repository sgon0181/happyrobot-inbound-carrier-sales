# Carrier Sales Service

Prototype of [`ARCHITECTURE.md`](../ARCHITECTURE.md), built on the existing TMS,
booking and pricing core. Python 3.12 with FastAPI. Deployment state and measured
limits are recorded in the root `PROTOTYPE_REPORT.md` when this run finishes.

## Run the tests

From the repository root:

```bash
python3 -m unittest discover -s service/tests -t .
```

The tests run offline. They use a local fake TMS over real TCP, and importing them blocks every connection except to this machine, so they cannot reach the real TMS.

## What is here

| Path | Job |
|---|---|
| `adapters/tms/protocol.py` | Encodes requests and strictly parses replies. No network. |
| `adapters/tms/client.py` | Async client: bounded read retries, and one guarded send for bookings. |
| `adapters/tms/mapping.py` | The one mapping from TMS fields to the PDF's load fields. |
| `adapters/tms/fake.py` | A fake TMS with fault injection. It follows observed behaviour, including `PENDING` replies. |
| `core/booking.py` | Booking states, the rep's decision, reconcile and restart recovery (section 6.6). |
| `core/pricing.py`, `policy/pricing-v1.json` | The versioned pricing policy (section 6.5). |
| `core/negotiation.py` | Counter rounds. |
| `core/loads.py` | Which loads may be offered. |
| `core/calls.py`, `api/app.py` | Call gates, authenticated API and transcript collection. |
| `adapters/confirmation.py` | Strict booking permission from native platform messages. |
| `adapters/twin/` | Durable canonical CAS state and projected business tables. |

## Safety rules

- **Live `LOAD_BOOK` is off by default.** It needs `booking_enabled=True` in `TmsSettings`, and each send spends a load permanently.
- **`max_rate` stays inside the service.** It is excluded from `repr`, and `agent_view` is the only booking data the voice agent gets.
- **`InMemoryBookingStore` says nothing about Twin.** Real canonical CAS contention was tested separately, with eight requests and one winner. The fallback and its limits are recorded below.

## Receipt and state handling

The prototype corrects the phase 1 gaps exposed by the harness:

- Received bytes, phase, error class and digest survive a failed reply.
- A connection that never opens is rejected before send, resulting in FAILED.
- Receipt storage retries independently; the final fallback is restricted service
  evidence logging, never another booking send.
- ACK_PENDING and UNKNOWN share the neutral `senior_review` agent status.
- Confirm requires ACK_PENDING or CONFIRMED, and never performs a TMS write.

## Prototype operation

`make test` runs offline tests. `make deploy` builds and deploys only the approved
Fly app. Provision the `proto_` Twin tables first. Runtime configuration
comes from ignored `.env` or process secrets. Do not import tests in a live
process, because their network guard deliberately blocks external connections.

`BOOKING_ENABLED` defaults off. The live BookingStore additionally permits only
MC 138328, excludes protected inventory, caps this campaign at three durable
send reservations, and closes the original authorization after its first real
acknowledged receipt. Any follow-up needs a new appended authorization tied to
one fresh load and the unchanged prior intent ledger. Its consumption is
atomic with the new send intent. No booking retry or namespace reset is supported.

The owner call saved a complete PENDING receipt but failed caller consent.
Price agreement alone no longer authorizes a live send. The first booking tool
request records a native user-turn anchor and returns the exact load-and-total
question. A subsequent request requires a fresh explicit affirmative answer,
with complete non-interrupted dialogue fetched by the service. Missing or
ambiguous evidence fails closed. This new gate passed offline replay and
regression checks. A native simulated conversation also proved that the live
platform exposes same-session messages while active: clarification failed and
a later explicit yes passed. All business tools were mocked in that test.
The subsequent real owner call proved the corrected consent path and produced
LD01085's PENDING receipt at 2950. Its follow-up permission is consumed. Exactly
two real write intents exist, with no permission for another send. Keep the
original call in caller-consent review, excluded from the successful-handoff
metric. Full handoff speech was repaired and checked separately without a send.

The owner configured Gmail SMTP privately through
`python -m service.scripts.set_email_credential`. The deployed transport accepted
a new code email on a synthetic call. Actual inbox receipt and human code entry passed on the second owner call. Never put the app password in chat or Git.

`make warm` keeps the existing single Fly Machine available during active QA;
`make idle` restores auto-stop. The owner budget is USD3 total, and Fly has no
hard spending cap. See [the session plan](../docs/fly-session-budget.md).
Card setup is complete and the single VM passed a continuous-runtime check
beyond five minutes with the same boot and instance.

Twin's SQL endpoint rejects data-modifying CTEs, and its runtime role cannot
create tables. The approved last-resort implementation uses one canonical
version-checked JSONB row in `proto_calls`, behind the same storage interface.
Eight physical business tables plus `proto_booking_claims` are monotonic read
models. The operations app reads the canonical service API, since the native
Twin gateway remains Failed. This is an explicit prototype deviation from
normalized atomic storage, not a claim that the original schema was proven.

Receipt captures use a private local journal plus Twin and a restricted log
fallback. Container files are ephemeral. Export captures before replacement;
this implementation does not promise cross-machine journal durability.

Price questions and pending permission are nonterminal. The revised voice
contract was tested against incomplete questions, a genuine counter, repeated
rate questions and a fresh yes through the real consent endpoint on synthetic
state. Calls with no recorded business result close as ended_without_booking;
that value does not assert who ended the call. See
[the clarification record](../docs/clarification-fix.md).
