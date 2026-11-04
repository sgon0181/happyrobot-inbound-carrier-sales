# Friday review proposal

The published App, workflow and existing ZIP are the November 5 baseline. This branch contains a candidate for a brokerage pilot. The [business and IT build description](build-description.md), [prospect email draft](submission.md), [recording cues](proposal-demo.md) and [assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf) locate the deliverables.

## What changes for the desk

The service binds the operating terms to an offer and repeats the check at submission. A changed pickup ZIP, lane, appointment, equipment, commodity, weight, dimensions or notes requires a fresh agreement. The posted rate can change independently. The agreed payment must still fit the current ceiling. An older row without sufficient terms requires fresh review.

The native App has two Overview reports. **Recorded trial** joins the native call inventory to Twin. Follow a conversion count to its calls and price pairs. Empty searches and verified calls that never searched call for different follow-up. **Current desk** shows the oldest reservation awaiting senior review, acknowledged requests, ambiguous sends and seven-day conversion for real-tagged activity. The Reservations queue also includes historical trials. Demand separates open calls and calls without end evidence from verified carriers known to have left.

## Pilot configuration and rollback

1. Use an isolated HappyRobot workspace, Ops App and cloud service with separate Twin data, service keys and test TMS. The service writes to its workspace's production Twin environment. OPS_SERVICE_URL must point to the intended HTTPS service and HR_PLATFORM_URL to the platform that authenticates the App.
2. Set the App's server-only OPS_REP_SUBJECTS to a comma-separated list of exact subject IDs from platform-verified App users. Other users can investigate records. Even an administrator needs an assignment to mutate a booking. The audit event records the authenticated subject.
3. The approved demo sends email to the candidate inbox. For a customer pilot supply OTP_CONTACTS_JSON as a protected service setting containing independently verified MC-to-email mappings. For example, {"138328":"dispatch@example.test"} is a fixture. In roster mode an unlisted carrier receives no mail. New addresses require independent onboarding. The caller cannot change a destination.
4. For an isolated booking exercise explicitly set CALL_COHORT=real and LIVE_BOOKING=true on the proposal service. Use a fresh call to create a reservation. Historical synthetic and unclassified reservations cannot be sent. From the App open that reservation, compare its terms and call evidence, select **Confirm** and approve the request. Competing reps are checked against the version they reviewed.
5. A PENDING receipt with matching load, reference and valid timestamp is an acknowledgement. Only a matching BOOKED receipt yields final confirmation. After an ambiguous send, reconcile by reading and contact the TMS operator if needed. Reconciliation cannot write a duplicate booking or promote an inventory status to a booking receipt. To stop new sends, switch LIVE_BOOKING=false. The TMS has no documented cancellation for an accepted send.

The service builds with the repository Dockerfile. For an isolated Fly app, copy the config with a distinct app name. After provisioning its tables and secrets, run `fly deploy --config <proposal-config> --app <proposal-app> --ha=false`. Native App and workflow promotions are separate from this command.

## Challenge rubric

| Requirement | Acceptance evidence | Scope |
| --- | --- | --- |
| Inbound web call, conversational driver experience, mocked transfer | Genuine Version 8 Werner audio, [call decisions and scripted checks](../happyrobot/README.md) and [recording cues](proposal-demo.md). | A spoken handoff is distinct from live telephony transfer. |
| Active authority, identity and OTP before freight | FMCSA gate, carrier readback, protected email destination, attempt limits and [HTTP abuse cases](../service/tests/test_verify.py). | Shared candidate inbox demonstrates the approved demo. Customer pilot requires its trusted roster. |
| Freight fields and legacy TMS | [Wire client](../service/adapters/tms/client.py) and [matching](../service/selling.py) recheck lane and details, skip unquotable freight and try later eligible loads within the tool deadline. | Unrecognized operating text requires rep review. Currency scale and timezone are documented assumptions. |
| Rate ceiling, privacy and bounded rounds | [Pricing](../service/core/pricing.py), [round decisions](../service/sale_decisions.py) and [negotiation journeys](../service/tests/test_selling.py). A rising ask cannot earn more than the carrier's prior ask on unchanged terms. Final refusal spends no fourth round. | The tool distinguishes a transport retry from a fresh response to the final quote. Private ceilings stay outside the voice payload. |
| Rep handoff, single booking write and audit | [App permissions](../ops-app/src/lib/rep-access.ts), [rep actions](../service/rep_actions.py), [historical TMS fixtures](tms/fixtures/booking-replies.json) and versioned Twin events. | Wire bytes stay in restricted Twin on a successful receipt save. A failed save returns safe identifiers and digest for recovery. Luke accepted PENDING handling. |
| Native App and data | Searchable Reservations, Bookings, Calls and Demand. Twin stores state and transitions. The authenticated HappyRobot App reads through the keyed service. | Mutation requires a specific rep assignment. Media access and retention follow workspace permissions. |
| North Star, standard, edge and adversarial QA | Verified calls with a reservation, agreement after matching, price movement and exceptions. [KPI definitions](kpis.md), [QA evidence](qa-results.md) and [desk tests](../ops-app/tests/proposal-desk.test.cjs). | Eighteen of 19 agreements came from one MC. Neither gross margin, speech safety nor avoided headcount can be inferred from the sample. |
| Peak strain, outages and resilience | [Peak-shift test](../service/tests/test_peak_shift.py) runs 12 concurrent API journeys, a malformed TCP read, 24 competing approvals and 12 single booking writes yielding simulated PENDING. Reads are budgeted and share three slots per process. | The 49 recorded trials did not overlap. The concurrency test uses fake dependencies plus a real loopback TCP listener. |
| Deployment, auth and delivery | Keyed service endpoints including health, bounded requests, verified App identity, [Docker](../Dockerfile), [single-command deployment](../Makefile), [reviewer guide](reviewer-guide.md) and [submission package](submission.md). | Native environment setup, contact enrollment, operator assignment and customer load qualification require separate configuration. |

## Reproduce the results

Run `make check` with Python 3.12. In ops-app run `npm ci && npm test && npm run lint && npm run build && npm run typecheck`. Run the concurrent booking scenario alone with `python -m pytest -q service/tests/test_peak_shift.py`.

Run `python -m service.tests.peak_profile` to measure MC verification with the actual 0.25-second Twin pacing setting, one dashboard refresh and a 12-second tool deadline. A new call now inserts the initial audit event and applies the authority result with a version check. A competing write forces a reread. Both events remain durable. These figures came from one local before/after run with a fake authority and Twin adapter and exclude voice latency.

| Arrival pattern | Baseline eligible, p95, SQL statements | Proposal eligible, p95, SQL statements |
| --- | --- | --- |
| 8 start together | 8/8, 8.29 s, 34 | 8/8, 4.02 s, 18 |
| 15 start together | 1/15, 12.01 s, 48 before deadline | 15/15, 7.53 s, 32 |
| 15 start 1.5 s apart | 15/15, 1.26 s, 62 | 15/15, 0.26 s, 32 |

The 12-journey wire test exercises data isolation and duplicate approvals. The paced experiment measures one authority operation. Customer acceptance requires a staffed trial with real arrival timing, answer and hold telemetry, real contact routing and monitoring of confirmed versus uncertain submissions.
