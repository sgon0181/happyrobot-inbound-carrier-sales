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

## Safety rules

- **Live `LOAD_BOOK` is off by default.** It needs `booking_enabled=True` in `TmsSettings`, and each send spends a load permanently.
- **`max_rate` stays inside the service.** It is excluded from `repr`, and `agent_view` is the only booking data the voice agent gets.
- **`InMemoryBookingStore` says nothing about Twin.** It shows what the `BookingStore` interface needs: an atomic claim and a conditional update. T-1 proved both on Twin probe rows, and the real schema must still show them.

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
Fly app. Provision the eight `proto_` Twin tables first. Runtime configuration
comes from ignored `.env` or process secrets. Do not import tests in a live
process, because their network guard deliberately blocks external connections.

`BOOKING_ENABLED` defaults off. The live BookingStore additionally permits only
MC 138328, excludes protected inventory, caps this campaign at three durable
send reservations, and closes further sends after its first real acknowledged
receipt. No booking retry or namespace reset is supported.
