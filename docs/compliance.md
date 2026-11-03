# PDF compliance audit

Every requirement in [the assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf), checked against `main` (`ca0c92c`), the owner's two test calls of 2026-11-03 (runs `1e88615d` and `d86f4b9e`), the live service, workflow Version 2 and the operations app (Build 17) on 2026-11-03. Written by Claude for the owner's review; Codex is asked to check it independently.

**Status:** Met (built, with evidence) · Partial (built, but with a known weakness or no measurement) · Gap (not done) · Owner (only the owner can do it).

## Page 1: the problem

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 1.1 | Missed calls and long holds at peak hours | The agent answers every web call | 4 real calls answered; median 27 s to the first offer | Partial: concurrency at peak is not measured (§13 capacity target unproven) |
| 1.2 | Inconsistent negotiation: dispatchers apply different ceilings | One versioned pricing policy prices every load from `MAX_BUY` (D-4, D-10) | `test_pricing`, `test_negotiation` | Met |
| 1.3 | Manual FMCSA lookups | `verify_carrier` checks FMCSA automatically, failing closed | `test_carrier_policy`, `test_fmcsa`; a real ineligible carrier turned away | Met |
| 1.4 | No audit trail of what was said, offered or agreed | Each call row keeps an event per step; the agent writes a summary at close | Call log in the dashboard | Partial: our offers and the agreement are recorded, but the carrier's own counter-offers are not (only the latest ask, internally), and no transcript is kept in Twin |
| 1.5 | Dispatcher burnout | No dispatcher in the first leg; a rep only confirms | The real call on run `ddae86e8` | Met |
| 1.6 | Carrier calls any time, gets verified, an offer, negotiates, is handed to a rep, with no dispatcher | The whole voice flow | Run `ddae86e8`, then the rep's Confirm of LD01080 | Met |

## Pages 2 and 3: the process

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 2.1 | The carrier calls in | Web call trigger, no phone number | Workflow `01a18119` Version 2 | Met |
| 2.2 | Check the MC against FMCSA for active authority; if it fails, the call ends | `verify_carrier`; the prompt ends the call on ineligible | Evals E1, E2; real call `05c37be5` | Partial: on the owner's test call `1e88615d` the MC was misheard as 1383208, FMCSA found nothing, and the agent ended the call without reading the number back or asking again. A misheard MC turns away an eligible carrier |
| 2.3 | A confirmation code by email or SMS before proceeding, for carriers not already in the system | Every call, by email (D-9, D-12, approved by Luke) | `test_verify`; evals S2, E3, A2 to A4 | Met, stricter than asked: every carrier, not only new ones |
| 2.4 | Search loads by lane and equipment; pitch the details | `find_loads`: `LOAD_QUERY`, then `LOAD_GET`, open loads with a future pickup only | `test_selling`; eval S3; real call | Met |
| 2.5 | The 14 load fields | Mapped from TMS fields (`mapping.py`), dimensions in inches; the agent gets all but `loadboard_rate` and `max_rate` | `test_mapping`, `test_loads` | Met; `loadboard_rate` withheld from the agent on purpose, so it never anchors above our offer |
| 2.6 | Accept, reject or counter; hold the line at `max_rate`; no agreement ends the call; agreement reserves tentatively | `negotiate`: three rounds, a cap under the ceiling, a reservation row | `test_negotiation`, `test_selling`; evals S4, S5, E5, E6 | Partial: the service is correct, but the live prompt sometimes closes without calling `negotiate` (evals S5, E6, E7 fail on Version 2; Version 3 fixes most) |
| 3.1 | Handoff to a senior rep who confirms the booking; transfers are mocked | The agent says it is transferring; the rep confirms in the dashboard, which sends `LOAD_BOOK` (D-22) | Rep Confirm of LD01080 returned a reference | Met. "Collects additional documentation" is out of scope for a mocked transfer |
| 3.2 | Log carrier MC, load ID, agreed rate, outcome and notes | Call row: `mc`, `agreement`, derived outcome, `summary` | Call log | Met; "notes" is the agent's closing summary |
| 3.3 | Legacy TMS over TCP, unreliable: handle timeouts and malformed replies gracefully | Strict parser, bounded retries for reads, no retry for bookings | `test_protocol`, `test_client`, `test_book` against a fault-injecting TCP server | Met |
| 3.4 | FMCSA, HappyRobot platform, senior rep queue mocked | As above; the rep queue is the dashboard | | Met. SMS is not used; codes go by email, as Luke approved |

## Page 4: additional requirements

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 4.1 | Enforce `max_rate`; never disclose it, directly or indirectly | The service prices and checks every number; the agent never receives the ceiling; Confirm rechecks it | INV-1, INV-2 tests; eval A1, A6 | Met, with a documented limit: probing can narrow the cap boundary (architecture §9) |
| 4.2 | OTP after the authority check, before load matching; a hard requirement | The service refuses a search until the call's own row shows both | INV-3 tests; evals A2, A4 | Met |
| 4.3 | All call activity in Twin; external databases only if justified | Twin tables `calls` and `bookings` hold everything | Live rows | Met. Transcripts stay in HappyRobot's own run records, not copied to Twin (security §12) |
| 4.4 | An app in HappyRobot Apps with key signals and actions for the operations manager, no raw platform logs | Operations app, Build 17 | Live; owner reviewed it 2026-11-03 | Partial: works, but the rep cannot see the lane or pickup, labels are raw codes, the title says "[CODEX LAB ONLY]", tables are cut off, and Confirm is offered while live booking is off, then refused after the click (owner's test booking LD01088). See [the redesign plan](plans/dashboard-redesign.md) |
| 4.5 | Northstar KPIs, a scripted suite of standard and edge cases, adversarial cases; results documented and presented | KPIs in the dashboard and architecture §14; 19 evals; [QA results](qa-results.md) | Folder "QA slice 5 (all tools mocked)" | Partial: the evals are mocked single decisions; the owner's own QA with real test calls is not done; nothing presented yet |
| 4.6 | Docker; one command deploys to the customer's cloud of choice | `Dockerfile`; `make deploy` | Deployed to Fly.io several times on 2026-11-03 | Met |

## Page 5: other considerations

| # | The PDF says | Where it is met | Evidence | Status |
|---|---|---|---|---|
| 5.1 | Direct, efficient, conversational: carriers are on the road | The prompt asks for brief, natural speech | Owner's real calls | Partial: not measured (no call-length or turn count, no rubric). On test call `1e88615d` the agent stayed silent for 21 seconds until the caller spoke (no opening line is set), and refused with no reason |
| 5.2 | At most three counters; no deal after three: close professionally, log as failed negotiation, no transfer | The service enforces rounds and records `negotiation_failed` | INV-4 tests; eval E6 | Partial: on Version 2 the agent can close without asking `negotiate`, so the call is logged as ended, not failed (eval E6) |
| 5.3 | Every endpoint authenticated; the OTP flow resists social engineering | Two keys, each opening only its routes; the code gate is in the service | Live probes: 401 for no, wrong or the other key; evals A2 to A4 | Met |
| 5.4 | Web call, no phone number | Web call trigger | | Met |

## Page 5: deliverables

| # | Deliverable | State | Status |
|---|---|---|---|
| D1 | Summary email: what was built and next steps | Draft in [submission.md](submission.md) | Owner: review once QA is done |
| D2 | Build description for IT and business review | Draft in [build-description.md](build-description.md); the form asks for a file (PDF) | Owner: review once QA is done |
| D3 | Repository link; private; reviewers invited | Private on GitHub; no reviewer invited; the form also accepts a .zip | Owner |
| D4 | HappyRobot workflow link | Workflow `01a18119`; web call page at platform.happyrobot.ai/deployments/6oaskq84xpfc | Owner: choose which link to give |
| D5 | Walkthrough video, about 5 minutes: live demo, dashboard, QA results | Not made | Owner |

## Gaps, in the order I would close them

| # | Gap | Fix | Who |
|---|---|---|---|
| G1 | The agent can close a call without asking `negotiate` (2.6, 5.2) | Publish Version 3 after the owner's QA confirms it; add a live test call for the take-it-or-leave-it case | Owner decides; Claude publishes on approval |
| G1b | The agent opens in silence, ends the call on a misheard MC, and refuses with no reason (2.2, 5.1) | In the same prompt version as G1: an opening line, read the MC back before checking it, ask once more on not found, give a plain reason on ineligible. Then rerun the evals and a test call | Claude drafts; owner decides with G1 |
| G2 | The rep cannot judge a deal: no lane, pickup or carrier name (4.4) | Redesign pieces 1 and 2 | Claude, approved |
| G3 | The dashboard looks unfinished (4.4), and offers Confirm while live booking is off | Redesign pieces 3 to 7; the service tells the app whether live booking is on, and the app shows it and disables Confirm | Claude, approved |
| G4 | The carrier's counter-offers are not in the audit trail (1.4) | Record each ask on the `negotiate` event (a `selling.py` change) and show it in the call's timeline | Claude, needs approval |
| G5 | QA is mocked and not the owner's (4.5) | The owner's test plan and real test calls, with calls marked as tests | Owner, Claude supports |
| G6 | Peak-hour concurrency unproven (1.1) | A load test against a test copy, never the live TMS booking path | Claude, needs approval |
| G7 | Carrier experience unmeasured (5.1) | Call length and turns per call from HappyRobot's run data, in QA results | Claude, after G5 |
| G8 | Deliverables not final (D1 to D5) | After G1 to G5 | Owner, Claude drafts |

## Not gaps, but worth stating

- Every carrier gets a code, not only new ones (2.3): stricter than the PDF, and simpler to defend.
- The booking is sent at the rep's Confirm, not during the call (3.1, D-22): the PDF's process has the rep confirm, and the TMS has no cancel.
- Every live booking returns `PENDING`, never `BOOKED`: the dashboard shows the TMS's own status and never counts `PENDING` as confirmed. Luke's answer (Q8) is still open.
- Page 1 says dispatchers "hand off confirmed bookings" to a rep, while page 3 has the rep confirm. We follow page 3, where the steps are spelled out.
