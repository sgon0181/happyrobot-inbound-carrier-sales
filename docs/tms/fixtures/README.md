# Sanitized TMS reply fixtures

[`booking-replies.json`](booking-replies.json) contains six minimal replies from the 2026-10-31 booking experiments. Four are reference-bearing `PENDING` acknowledgements, one is an explicit fractional-rate rejection, and one is the later deliberate duplicate probe. Read the [evidence and inventory](../../tms-contract.md#booking-experiments-2026-10-31) before interpreting them.

These are data for offline parser/domain tests, not commands to replay. `raw` uses JSON escapes for actual CRLF bytes. Synthetic `FIXTURE` booking references replace the originals; the original padding elsewhere, field names, status, timestamps and error text remain. The capture path and SHA-256 identify the ignored source packet. No host, port, token, portal link, password or live carrier contact is included.

`agreed_rate_text` records the historical input associated with a reply. It is not a recommended price. A complete `PENDING` acknowledgement is `ack_pending`, not `confirmed` or transport-`unknown`. `ALREADY_BOOKED` does not prove final confirmation or carrier/rate ownership. The explicit rejection followed by its integer control is distinct from automatically retrying an uncertain write.

There is no real `BOOKED` fixture. Any future synthetic confirmation fixture must be labelled as simulated. Reading this JSON is offline and does not require the ignored evidence folders or credentials. The original lab's 37 tests remain historical results, not tests shipped or executed by this fixture file.
