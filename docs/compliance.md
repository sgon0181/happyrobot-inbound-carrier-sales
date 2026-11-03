# PDF compliance audit

Every requirement in [the assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf), checked against `main`, the owner's two test calls of 2026-11-03 (runs `1e88615d` and `d86f4b9e`), the live service, workflow Version 2 and the operations app (Build 17) on 2026-11-03. Written by Claude, checked independently by Codex on 2026-11-03 (at `e00ef94`), and corrected from that review. The one point where Claude and Codex disagree is marked in row 4.1.

**Status:** Met (built, with evidence) · Qualified (met only with the stated limit) · Partial (built, with a known weakness) · Gap (not done). Who acts is said separately; a deliverable waiting on the owner is still Partial or Gap.

## Page 1: the problem

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 1.1 | Missed calls and long holds at peak hours | The agent answers web calls | 4 real calls recorded; median 27 s from the first service request to the first offer, which excludes the greeting and MC collection | Partial: four calls show calls are answered, not that every call is; concurrency at peak is not measured |
| 1.2 | Inconsistent negotiation: dispatchers apply different ceilings | One versioned pricing policy prices every load from `MAX_BUY` (D-4, D-10) | `test_pricing`, `test_negotiation` | Qualified: one policy is enforced; `MAX_BUY` as the ceiling is a documented assumption (D-10) |
| 1.3 | Manual FMCSA lookups | `verify_carrier` checks FMCSA automatically, failing closed | `test_carrier_policy`, `test_fmcsa`; a real ineligible carrier turned away | Met |
| 1.4 | No audit trail of what was said, offered or agreed | Each call row keeps an event per step; the agent writes a summary at close | Call log in the dashboard | Partial: our offers and the agreement are recorded, but the carrier's own counter-offers are not (only the latest ask, internally), and no transcript is kept in Twin |
| 1.5 | Dispatcher burnout | No dispatcher in the first leg; a rep only confirms | The real call on run `ddae86e8` | Qualified: an autonomous first leg is shown; reduced burnout is not measured |
| 1.6 | Carrier calls any time, gets verified, an offer, negotiates, is handed to a rep, with no dispatcher | The whole voice flow | Run `ddae86e8`, then the rep's Confirm of LD01080; test run `d86f4b9e` | Partial: the full path works, but the live prompt's known failures (2.6, 2.2) mean it does not yet work reliably |

## Pages 2 and 3: the process

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 2.1 | The carrier calls in | Web call trigger, no phone number | Workflow `01a18119` Version 2 | Met |
| 2.2 | Check the MC against FMCSA for active authority; if it fails, the call ends | `verify_carrier`; the prompt ends the call on ineligible | Evals E1, E2; real call `05c37be5` | Partial: on the owner's test call `1e88615d` the MC was misheard as 1383208, FMCSA found nothing, and the agent ended the call without reading the number back or asking again. A misheard MC turns away an eligible carrier |
| 2.3 | A confirmation code by email or SMS before proceeding | Every call, by email to the demo inbox (D-9, D-12, approved by Luke) | `test_verify`; evals S2, E3, A2 to A4 | Met. Page 2 mentions new carriers, but page 4 makes the code a hard requirement with no exception for returning carriers, so every call gets one |
| 2.4 | Search loads by lane and equipment; pitch the details | `find_loads`: `LOAD_QUERY`, then `LOAD_GET`, open loads with a future pickup only | `test_selling`; eval S3; real call | Met |
| 2.5 | The 14 load fields | Mapped from TMS fields (`mapping.py`), dimensions in inches; the agent gets all but `loadboard_rate` and `max_rate` | `test_mapping`, `test_loads` | Met; `loadboard_rate` withheld from the agent on purpose, so it never anchors above our offer |
| 2.6 | Accept, reject or counter; hold the line at `max_rate`; no agreement ends the call; agreement reserves tentatively | `negotiate`: three rounds, a cap under the ceiling, a reservation row | `test_negotiation`, `test_selling`; evals S4, S5, E5 to E8 | Partial: the service is correct, but on the live Version 2 the agent can close without calling `negotiate`, can say a booking is being confirmed (E7), and can pick a number from a vague range and send it as the carrier's ask (E8). Version 3 fixes most of this, unpublished |
| 3.1 | Handoff to a senior rep who confirms the booking; transfers are mocked | The agent says it is transferring; the rep confirms in the dashboard, which sends `LOAD_BOOK` (D-22) | Rep Confirm of LD01080 returned a reference | Qualified: the mocked handoff and the rep's submission work. A `PENDING` reference does not prove a final booking. Collecting documentation is left out of this proof of concept, our scope choice |
| 3.2 | Log carrier MC, load ID, agreed rate, outcome and notes | Call row: `mc`, `agreement`, derived outcome, `summary`, all in Twin | Call log | Partial: the fields exist, but notes are the agent's closing summary, so a dropped or unclosed call has none, and a close can arrive with no summary. The PDF has the dispatcher log in the TMS; the TMS has no logging command and page 4 requires Twin, so we log in Twin, an interpretation |
| 3.3 | Legacy TMS over TCP, unreliable: handle timeouts and malformed replies gracefully | Strict parser, bounded retries for reads, no retry for bookings | `test_protocol`, `test_client`, `test_book` against a fault-injecting TCP server | Met |
| 3.4 | FMCSA, HappyRobot platform, senior rep queue mocked | As above; the rep queue is the dashboard | | Met. SMS is not used; codes go by email, as Luke approved |

## Page 4: additional requirements

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 4.1 | Enforce `max_rate`; never disclose it, directly or indirectly | The service prices and checks every number; the agent never receives the ceiling; Confirm rechecks it; the cap sits a load-specific 2 to 6% under the ceiling, so it cannot be calculated | INV-1, INV-2 tests; evals A1, A6 | Qualified: enforcement is Met. Disclosure: the ceiling never leaves the service, but any negotiation reveals that the ceiling is at or above the final offer, and probing can narrow it (architecture §9). Claude reads the PDF as forbidding disclosure, which no negotiation can avoid entirely; Codex would mark this Partial. The residual risk is stated, not hidden |
| 4.2 | OTP after the authority check, before load matching; a hard requirement | The service refuses a search until the call's own row shows both | INV-3 tests; evals A2, A4 | Met |
| 4.3 | All call activity in Twin; external databases only if justified | Twin tables `calls` and `bookings` | Live rows | Partial: no external database, but call activity is incomplete in Twin. Missing: the carrier's asks (only the latest survives, internally), the load details offered, the code email being sent, and any call that ends before its first tool request. The transcript stays in HappyRobot's run records |
| 4.4 | An app in HappyRobot Apps with key signals and actions for the operations manager, no raw platform logs | Operations app, Build 17 | Live; owner reviewed it 2026-11-03 | Partial: works, but the rep cannot see the lane or pickup, labels are raw codes, the title says "[CODEX LAB ONLY]", tables are cut off, and Confirm is offered while live booking is off, then refused after the click (owner's test booking LD01088). See [the redesign plan](plans/dashboard-redesign.md) |
| 4.5 | Northstar KPIs, a scripted suite of standard and edge cases, adversarial cases; results documented and presented | KPIs in the dashboard and architecture §14; 19 evals; [QA results](qa-results.md); two owner test calls | Folder "QA slice 5 (all tools mocked)" | Partial: the suite exists and found real failures, but results are not yet presented, the QA report's numbers are stale, and KPI definitions are loose: time to first offer starts at the first service request, "calls answered" counts recorded calls, "reserved handoffs" counts reservations, not spoken handoffs |
| 4.6 | Docker; one command deploys to the customer's cloud of choice | `Dockerfile`; `make deploy` | Deployed to Fly.io several times on 2026-11-03 | Met |

## Page 5: other considerations

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 5.1 | Direct, efficient, conversational: carriers are on the road | The prompt asks for brief, natural speech | Owner's real calls | Partial: not measured (no call-length or turn count, no rubric). On test call `1e88615d` the agent stayed silent for 21 seconds until the caller spoke (no opening line is set), and refused with no reason |
| 5.2 | At most three counters; no deal after three: close professionally, log as failed negotiation, no transfer | The service enforces rounds and records `negotiation_failed` | INV-4 tests; eval E6 | Partial: on Version 2 the agent can close without asking `negotiate`, so the call is logged as ended, not failed (eval E6) |
| 5.3 | Every endpoint authenticated; the OTP flow resists social engineering | Two keys, each opening only its routes; the app checks the signed-in user; the code gate is in the service | Live probes: 401 for no, wrong or the other key; evals A2 to A4 | Met, within demo scope |
| 5.4 | Web call, no phone number | Web call trigger | | Met |

## Page 5: deliverables

| # | Deliverable | State | Status |
|---|---|---|---|
| D1 | Summary email: what was built and next steps | Draft in [submission.md](submission.md); links unfinished, and some claims need correcting | Partial, owner to finish |
| D2 | Build description for IT and business review | Draft in [build-description.md](build-description.md). It overstates: ceiling confidentiality, "every call is recorded", one voice failure where there are several, and "spends a load for good" where the evidence shows no cancel and lasting state, not permanence | Partial, to rewrite after QA |
| D3 | Repository link; private; reviewers invited | Private on GitHub, not independently verified; no reviewer invited. The form also accepts a .zip, but the PDF asks for a link | Partial, owner to invite |
| D4 | HappyRobot workflow link | The workflow exists; its link is not yet in the submission. Give the workflow link separately from the web call page (platform.happyrobot.ai/deployments/6oaskq84xpfc) | Partial, owner to choose |
| D5 | Walkthrough video, about 5 minutes: live demo, dashboard, QA results | Not made | Gap, owner |

## What to close

### Needed to meet the PDF

| # | Gap | Fix | Rows |
|---|---|---|---|
| R1 | The agent can skip `negotiate`, say a booking is being confirmed, or pick a number from a vague range | Publish the corrected prompt (Version 3 plus R2) after the owner's QA | 1.6, 2.6, 5.2 |
| R2 | The agent opens in silence, ends the call on a misheard MC, and refuses with no reason | An opening line; read the MC back before checking it; ask once more on not found; a plain reason on ineligible | 2.2, 5.1 |
| R3 | Call activity is incomplete in Twin | Record each carrier ask and the load details offered on the call's events, the code email being sent, and a record for every call, including one that ends before its first tool request or without a close | 1.4, 3.2, 4.3 |
| R4 | The dashboard lacks what an operations manager needs to act | Lane, pickup and carrier in the rep queue; whether live booking is on, with Confirm disabled while off; readable labels; the App's title; no cut-off tables (redesign pieces 1 and 2, plus the live-booking state) | 4.4 |
| R5 | KPIs and QA are not ready to present | Precise KPI definitions (time to first offer from the call's start, calls recorded versus answered, reservations versus spoken handoffs); the owner's test runs; a corrected QA report | 4.5 |
| R6 | Deliverables unfinished | Email, build description, repository link and invitations, workflow link, video, written from the corrected facts | D1 to D5 |

### Recommended, beyond the PDF

| # | Recommendation | Why |
|---|---|---|
| X1 | The full dashboard redesign (redesign pieces 3 to 7) | Makes the app feel like a TMS a brokerage already uses |
| X2 | A capacity test, 12 calls of about 4 minutes at once | The page 1 problem is peak hours; nothing measures it yet |
| X3 | Carrier experience measures: call length and turns per call | Page 5 asks for a direct, efficient agent; this would show it |
| X4 | A fuller audit trail: the transcript, or a link to the run, on each call row | The page 1 problem is the missing audit trail |

## Not gaps, but worth stating

- Every carrier gets a code (2.3), because page 4 states the requirement with no exception for returning carriers.
- The booking is sent at the rep's Confirm, not during the call (3.1, D-22): the PDF's process has the rep confirm, and the TMS has no cancel.
- Every live booking returns `PENDING`, never `BOOKED`: the dashboard shows the TMS's own status and never counts `PENDING` as confirmed. Luke's answer (Q8) is still open.
- Page 1 says dispatchers "hand off confirmed bookings" to a rep, while page 3 has the rep confirm. We follow page 3, where the steps are spelled out.

## R3 local completion, awaiting rollout

The R3 candidate stores successful/failed code delivery, normalized search criteria, returned public pitch details, each heard and parsed ask, the approved response/round, reservation and rep decisions, and the workflow end report. Reconstruction and marked-ceiling/expected-code tests use only fake integrations. The app projects the actual string lanes and all captured public pitch fields. Rows 1.4, 3.2 and 4.3 remain Partial for the live system until deployment and Version 4 publication are approved and checked. No raw transcript is copied. Model speech, calls that never reach the end callback, failed Twin writes and absent closing summaries remain limits; an inferred quiet call is end_not_recorded, not a proven hangup.

E7 candidate: the service now returns truthful unavailability and an explicit search-again continuation. Unpublished Version 4 follows that result. It passes 18/18 mocked checkpoints, including eight repetitions of the unstable case; service tests cover no extra reads, no stale alternatives, no new round and no send. R1 remains pending deployment, workflow publication and owner voice acceptance; the candidate does not claim voice behavior is proven.
