# Carrier Sales Service

Phase 1 of [`ARCHITECTURE.md`](../ARCHITECTURE.md): the TMS adapter and the booking and pricing core. It has no endpoints yet, and it uses only the Python standard library. The deployed target is Python 3.12.

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

## Known gaps

Codex's live test exposed these, and they are fixed before phase 2 ([architecture section 11](../ARCHITECTURE.md#11-delivery-plan)):

- **Lost evidence:** on a timeout or reset, `TmsClient.book` keeps only the error type and discards any reply bytes already received.
- **False unknown:** a connection that never opens is `UNKNOWN`, which blocks the load for good. It should be `FAILED`, because nothing was sent.
- **Lost receipt:** if saving the receipt fails, the booking stays `SUBMITTING` and the receipt is gone.
- **Overclaiming:** `agent_view` says `request_accepted` on `UNKNOWN`. It should use the neutral status from D-18.
- **Confirm on `UNKNOWN`:** `confirm` still accepts these bookings, pending the owner's decision on D-18.

## Not built yet

Endpoints, authentication, the Twin, FMCSA and email adapters, Docker and deployment.
