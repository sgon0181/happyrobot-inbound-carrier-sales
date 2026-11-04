# Assignment compliance, submission candidate

Source: [the five-page assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf), reread on 2026-11-04. Workflow Version 7 (`67nko7p112j2`), Fly release 17 from `bf512aa`, and Carrier Sales App Build 20 are live. The owner approved publication of reviewed 9d7a149 and all remaining release/submission work. Booking sends remain off and calls stay synthetic. The current prompt passes 102/102 locked checkpoints. The App's 77-file archive matches the checkout and final 1280px views/panels pass. One focused Version 7 human call, owner video and reviewer-account access remain open.

Statuses: Met means implemented with the stated evidence. Qualified means demonstrated within a stated interpretation or limit. Partial means a material requirement or acceptance step remains open. Gap means absent. The build is a proof of concept, not a claim of production reliability. [QA results](qa-results.md) retains failures and versions; [submission.md](submission.md) lists the owner approval steps.

Ten Version 5 owner calls exposed partial amounts, invented final wording and poor endings. Eleven later Version 6 calls now show proactive hangup and stored close/end activity across refusals, agreements and failed negotiations. One split-amount intent failure (3825 recorded as 3800) and omitted operating notes led to the reviewed Version 7 fix, now published. The single focused acceptance call is specified in final-owner-checklist.md. Native checkpoints and text simulations do not prove voice behavior. Audio was not listened to in the latest review. [Release evidence](releases/2026-11-04-v7/README.md) and [QA](qa-results.md) retain the failures and limits. No new booking was sent.

## Page 1: problem and intended outcome

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 1.1 | Address missed calls and peak holds | Web calls and four historical real-cohort rows. Recorded calls and service-tool timing are defined in kpis.md. No answer-rate or peak-capacity measurement | Partial: capacity and every-call coverage unproven |
| 1.2 | Consistent negotiation ceilings | Versioned policy, service-enforced fresh terms, generated inputs and concurrency tests; MAX_BUY mapping is an assumption | Qualified |
| 1.3 | Automate FMCSA lookups | Authority policy, adapter tests and real eligible/ineligible responses | Met |
| 1.4 | Structured record of what was said, offered and agreed | Deployed service records each heard/normalized ask, approved response/round, public pitch, searches, code delivery and closing/end evidence. Row-only reconstruction tests pass | Partial: structured tool activity is not verbatim speech; undelivered callbacks and absent closing notes remain gaps |
| 1.5 | Reduce dispatcher burden | Autonomous first leg demonstrated in real and owner calls; rep reviews the reservation | Qualified: reduction in burnout or staffing cost not measured |
| 1.6 | Verify, match, negotiate and hand off without dispatcher | Historical full flow, 11 Version 6 timed call reviews, and Version 7 with 102/102 locked checkpoints | Partial: focused Version 7 split-amount/notes acceptance remains open; refusal and failed-path endings have Version 6 evidence |

## Pages 2 and 3: process

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 2.1 | Carrier calls in | HappyRobot web-call trigger, inbound agent | Met |
| 2.2 | Active FMCSA authority; end if ineligible | Service distinguishes ineligible from unavailable; name confirmation, MC correction and refusal paths pass the current Version 7 checkpoints | Qualified: authority/refusal implementation and checkpoints pass, with Version 6 refusal evidence. Misheard-MC and wrong-name human coverage remains limited, not a request to repeat the unchanged suite |
| 2.3 | Email or SMS confirmation before proceeding | Service code gate on every call, email destination fixed by configuration, approved demo inbox exception | Qualified: demonstrates inbox access, not legal carrier identity; page 4 has no returning-carrier exception |
| 2.4 | Match lane/equipment and pitch details | Fresh LOAD_QUERY/LOAD_GET, availability/pickup filters, public_view; HTTP journeys include three equipment/lane/carrier combinations. Owner calls exposed unlabeled pickup clocks and unclear equipment; deployed display fields have Version 6 voice evidence. Version 7 adds complete notes | Partial: Version 7 operating-note acceptance pending |
| 2.5 | Fourteen load fields | Mapping/models include the PDF fields. Agent sees the public allowlist excluding private max_rate and posted rate; rep sees posted alongside agreed payment | Qualified: intentionally restrict the agent's rate fields; currency/timezone assumptions remain documented |
| 2.6 | Accept/reject/counter, ceiling, tentative reservation | Atomic decisions and state limits hold in offline tests. Owner Version 5 calls demonstrated partial-rate agreements and an invented final-offer description. Version 6 voice checks validate status-specific wording; Version 7 adds explicit post-clarification confirmation | Partial: focused Version 7 amount-intent acceptance pending |
| 3.1 | Mock handoff to senior rep who confirms | Spoken mocked handoff; App rep Confirm sends once. Historical LD01080 has reference-bearing PENDING | Qualified: PENDING is acknowledgement, not final confirmation; no document-collection workflow is built |
| 3.2 | Log MC, load ID, rate, outcome and notes | Twin call/booking rows, per-row atomic events, reconstructed activity, optional closing notes and live end callback | Partial: E1/E2 closing omissions were fixed and pass later checkpoints; skipped close still leaves no notes, and callback delivery is not guaranteed. Twin instead of TMS logging is explicit because no logging command exists |
| 3.3 | Unreliable raw TCP handled gracefully | Bounded read retry budget, strict framing and loopback fault servers; booking uses one fresh connection within its total deadline and never retries | Met within recorded contract and injected faults |
| 3.4 | Platform, FMCSA, legacy TMS and mocked rep queue | Native voice, Twin and Apps; service adapters; rep queue and mocked transfer | Met |

## Page 4: additional requirements

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 4.1 | Enforce max_rate; never disclose directly or indirectly | Fresh rate checks and marked-value tests; expected ceiling withheld from agent. Known policy bands/observed offers can still constrain its value | Partial: enforcement implemented; absolute indirect secrecy is not proven. Earlier Qualified versus Partial disagreement is resolved conservatively here, without claiming the risk vanished |
| 4.2 | Code after authority, before matching, with no bypass | Same-call stored authority/code gates; unauthorized state/destination fields refused; adversarial checkpoints and native urgency refusal | Met within demo destination exception |
| 4.3 | All activity in native Twin | Deployed calls/bookings rows with atomic state/events, earlier asks and freed-load history | Partial: speech, refused no-op carrier changes and undelivered callback/write gaps remain outside the stored trail |
| 4.4 | HappyRobot Apps operational signals/actions without raw logs | Current production Build 20 and redesigned dashboard observed with sends off. Build 18 exact-source publication, captured terms/history and recovery evidence remain historical | Qualified: source is reported by Claude and archive-checked, not independently attested from production files. Final UI passes read-only checks; receipt recovery remains component-tested. No live booking action was clicked |
| 4.5 | Defined KPIs, standard/edge/adversarial tests, results documented and presented | kpis.md, qa-package.md, qa-results.md, historical checkpoints, seeded tests, nine HTTP journeys and two native full text conversations | Partial: package written; walkthrough presentation not yet recorded. Pressure run idle timeout is retained, not a successful closing |
| 4.6 | Docker and one-command cloud deployment | Dockerfile, make deploy and healthy Fly release 17 from `bf512aa` | Met within configured PoC environment; release performed by Claude after owner approval |

## Page 5: experience, boundaries and security

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 5.1 | Direct, efficient, conversational | Version 3 opening/name correction and one clean owner call; Version 4 standard text handoff. Pressure text run stalled for 141 s before idle timeout | Partial: greeting/correction/interruption limits remain; 11 Version 6 timed traces show proactive endings; no population efficiency claim |
| 5.2 | Up to three counters, failed close logged, no transfer | Service rounds across loads/MC changes and sticky failure; repeated E6 checkpoints and Version 6 human calls aa6da4fc/3f07545e | Met within observed traces: three-round/failure behavior, logged close, no transfer; no broad reliability claim |
| 5.3 | Authenticate every endpoint; resist OTP social engineering | Separate agent/ops keys, App verified session, live historical 401 probes and offline route tests; service gate independent of model | Met within PoC scope; shared inbox is not identity proof and cross-call abuse controls are deferred |
| 5.4 | Web call; no phone provisioned | Native web-call deployment | Met |

## Page 5: deliverables

| # | Deliverable | State | Status |
|---|---|---|---|
| D1 | Prospect email with build and next steps | Corrected prospect text in submission.md, five tailored next steps and links; owner approved final submission work | Partial: text ready; portal submission awaits real call/video |
| D2 | Business/IT build description | Updated build-description.md records this release and the identity, capture, ceiling, PENDING and reliability limits | Qualified: current PDF is generated and visually checked; final portal submission awaits video |
| D3 | Private repository and reviewer invitations | Private/default-main verified read-only on GitHub; only owner collaborator and zero pending invitations | Partial: owner authorized invitations, but intended reviewer identities have not been provided; source ZIP also prepared for portal review |
| D4 | Workflow link | Exact Version 7 editor and web-call links in submission.md; Version 7 is live | Qualified: publication complete; reviewer-account access still needs validation |
| D5 | About-five-minute video, demo, App and QA | walkthrough.md run sheet and required closing next steps | Gap: owner-recorded video and final URL absent |

## R1 to R6 completion and release boundary

| Item | Local completion | Remaining acceptance or owner action |
|---|---|---|
| R1 conversation correctness | Version 7 live, 51 checkpoints twice (102/102), 11 Version 6 timed call reviews; all failures retained | One focused split-amount/notes call with intact closing; do not repeat the Version 6 suite |
| R2 basic carrier experience | Version 3 greeting/name/MC corrections already implemented, no duplicate rebuild | Disclosed coverage limits for misheard MC and interruptions; no additional call required by the current finish plan |
| R3 activity capture | Structured activity, privacy/reconstruction tests, service route and end callback deployed | All 11 latest Version 6 calls have persisted close/end records. Speech and undelivered events remain outside guarantees |
| R4 essential dashboard | Carrier Sales Build 20 production observed; redesigned dashboard loads and sends are off. Build 18 acceptance remains historical | Source48ba398 is reported by Claude; archive and final 1280px UI verified. No new send |
| R5 QA and KPIs | Layers, versions, seeds, counts, failures and definitions documented; actual 100% service coverage | One focused Version 7 call and recorded presentation; capacity unproven |
| R6 handover | Corrected email, build description, links, reviewer instructions and walkthrough outline | Independent review and owner release/submission approval complete; video, identified reviewer access and final portal submission remain |

## Recommended work, not invented submission requirements

X1 full redesign pieces 3 to 7 requires owner review before further expansion. X2 capacity needs an agreed workload for a pilot, not an assumed 12-call rubric. X3 carrier-experience measures need actual audio/turn evidence. X4 a verbatim transcript is not required for the chosen structured-decision trail; adding one would need retention/redaction decisions. Optional A to C are analyzed separately and remain unimplemented without approval.

The page 1 phrase about confirmed bookings and page 3 rep-confirm step are ambiguous; D-22 follows the explicit tentative-reservation process. No official inventory quota, permanent load-consumption guarantee, finalization command or successful live BOOKED response is invented. Luke's Q8 remains open.

## Historical Version 4 checkpoint findings

The earlier owner-requested full 22-case rerun completed 58/66 passes, with 18/22 cases passing all three repetitions. At that point, S6 wrong-name recovery and E1/E2 closing-note tool use remained open. S5 has a narrower explicit-load-ID omission, with negotiate, close and truthful handoff observed. E7 and all six adversarial cases passed 3/3. That batch superseded any impression that the earlier 18/18 subset established the entire prompt's behavior. They do not replace the historical failures or prove audio reliability. No prompt change or publication accompanied the rerun. See qa-results.md and the pinned qa-v4 evidence files.

The subsequent fixed Version 4 passed 44/44, and the final Version 5 with only the approved carrier_locked line added passed 46/46. Version 5 was subsequently published, and is now replaced by Version 6. Those historical checkpoint results resolve the demonstrated S6/E1/E2 checkpoint defects; they do not erase the historical failures or prove human voice acceptance.
