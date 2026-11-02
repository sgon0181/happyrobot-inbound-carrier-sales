# FMCSA test-carrier ledger

Status 2026-10-31 (Australia/Sydney): five public records were checked through a HappyRobot native HTTP node, as a QCMobile docket lookup. MC 138328 was also checked directly from a Fly.io `iad` machine, with the same result, and was used on the live test call. These are saved observations, so recheck them near the demo because public records can change. Luke supplied no test MCs.

| Case | MC / DOT | Carrier | Checked (UTC) | Observed fields | Expected result |
|---|---|---|---|---|---|
| Authorized, used on the live test call | 138328 / 53467 | Werner Enterprises Inc | 03:29 | `allowedToOperate` Y, common A, contract A, `statusCode` A, `oosDate` null | Pass |
| Inactive | 134652 / 117201 | Mall Trucking and Freight Corp | 03:29 | `allowedToOperate` Y, common N, contract I, `statusCode` I | Reject |
| Inactive, used in the six historical TMS booking sends | 872144 / 2514144 | Ouza Transportation Inc | 03:25 | `allowedToOperate` Y, common N, contract I, `statusCode` I | Reject |
| Nonexistent | 99999999 | None | 03:30 | Empty `content` array | Reject as not found |
| API control only | 1515 / 44110 | Greyhound Lines Inc | 03:26 | `allowedToOperate` Y, common A, contract A, `statusCode` A, `oosDate` null | Passes the rule, but is a passenger carrier. Do not use in the demo. |
| Out of service | Not selected | | Not checked | | Needed before claiming this case |
| Broker-only authority | Not selected | | Not checked | | Needed for the conversation test |

Rechecked 2026-11-03 from the deployed service on Fly `iad`, with `core/carrier_policy.py`: 138328 eligible (`active_carrier_authority_verified`), 134652 refused (`registration_not_active`), 99999999 `not_found`. All three match the table.

Inactive carriers still show `allowedToOperate` Y, so that field alone proves nothing. A timeout or HTTP 403 is `fmcsa_unavailable`, not a not-found or inactive result. Passing this check does not prove who owns an MC or whether the carrier suits the freight, and it says nothing about OTP ownership.

When adding a case, record the timestamp and timezone, the source endpoint without `webKey`, the relevant fields and the eligibility decision. Keep only the minimum sanitized fields, with no contacts or credentials.

See [onboarding](onboarding.md#fmcsa-integration-starting-point) for the request shape and [architecture section 8](../ARCHITECTURE.md#8-verification-and-the-one-time-code) for the eligibility rule.
