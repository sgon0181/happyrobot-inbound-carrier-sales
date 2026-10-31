# FMCSA test-carrier ledger

Status 2026-10-31 (Australia/Sydney): **no live FMCSA test MC has been verified in this repository**. Luke supplied no test MCs. Do not treat handbook-example MC `872144`, which was used in TMS probes, as evidence of active carrier authority or OTP ownership.

| Required case | MC / DOT | Last checked | Evidence and expected result |
|---|---|---|---|
| Authorized common/contract carrier, allowed to operate, not out of service | Not selected | Not checked | Pending live verification and sanitized fixture. |
| Inactive/revoked authority or out of service | Not selected | Not checked | Pending live verification and sanitized fixture. |
| Nonexistent MC | Not selected | Not checked | Pending authoritative not-found response; a timeout is not nonexistence. |

Before using a case, record timestamp/timezone, source endpoint without `webKey`, exact relevant authority/operating fields, and the eligibility decision. Retain only the minimum sanitized response fields needed for the test; exclude contacts and credentials. Recheck status near the demo because public records can change. Broker-only authority does not satisfy the architecture's carrier-eligibility policy.

See [onboarding](agent-onboarding.md#fmcsa-integration-starting-point) for documented request/auth shape and unresolved field mapping, and [architecture §6.3](../ARCHITECTURE.md#63-verification-and-the-one-time-code) for the proposed gate. This ledger is an implementation checklist, not a claim that those tests passed.
