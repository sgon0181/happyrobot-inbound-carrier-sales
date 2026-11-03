# Assignment compliance, submission candidate

Source: [the five-page assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf), reread on 2026-11-03. This updates the e00ef94 audit against the local R1 to R6 candidate and retained live evidence. A local fix is not presented as deployed. Live workflow: Version 3. Candidate: unpublished Version 4. Live App: Build 17. Fly rollout and published-App visual acceptance are pending.

Statuses: Met means implemented with the stated evidence. Qualified means demonstrated within a stated interpretation or limit. Partial means a material requirement or acceptance step remains open. Gap means absent. The build is a proof of concept, not a claim of production reliability. [QA results](qa-results.md) retains failures and versions; [submission.md](submission.md) lists the owner approval steps.

## Page 1: problem and intended outcome

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 1.1 | Address missed calls and peak holds | Web calls and four historical real-cohort rows. Recorded calls and service-tool timing are defined in kpis.md. No answer-rate or peak-capacity measurement | Partial: capacity and every-call coverage unproven |
| 1.2 | Consistent negotiation ceilings | Versioned policy, service-enforced fresh terms, generated inputs and concurrency tests; MAX_BUY mapping is an assumption | Qualified |
| 1.3 | Automate FMCSA lookups | Authority policy, adapter tests and real eligible/ineligible responses | Met |
| 1.4 | Structured record of what was said, offered and agreed | R3 records each heard/normalized ask, approved response/round, public pitch, searches, code delivery and closing/end evidence. Row-only multi-round reconstruction tests pass | Partial: candidate built, not live; structured tool activity is not verbatim speech and missing callbacks/notes remain gaps |
| 1.5 | Reduce dispatcher burden | Autonomous first leg demonstrated in real and owner calls; rep reviews the reservation | Qualified: reduction in burnout or staffing cost not measured |
| 1.6 | Verify, match, negotiate and hand off without dispatcher | Historical full flow and owner Version 3 run 8167bb06; current checkpoints and standard text simulation | Partial: Version 4 voice acceptance and stalled refusal-path closing remain open |

## Pages 2 and 3: process

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 2.1 | Carrier calls in | HappyRobot web-call trigger, inbound agent | Met |
| 2.2 | Active FMCSA authority; end if ineligible | Service distinguishes ineligible from unavailable. Version 3 adds name confirmation and readback/correction for a not-found MC; owner transcript confirms name check | Partial: current S6 wrong-name checkpoint closes instead of requesting correction in 1/3 runs; misheard-MC voice check remains open |
| 2.3 | Email or SMS confirmation before proceeding | Service code gate on every call, email destination fixed by configuration, approved demo inbox exception | Qualified: demonstrates inbox access, not legal carrier identity; page 4 has no returning-carrier exception |
| 2.4 | Match lane/equipment and pitch details | Fresh LOAD_QUERY/LOAD_GET, availability/pickup filters, public_view; HTTP journeys include three equipment/lane/carrier combinations | Met |
| 2.5 | Fourteen load fields | Mapping/models include the PDF fields. Agent sees the public allowlist excluding private max_rate and posted rate; rep sees posted alongside agreed payment | Qualified: intentionally restrict the agent's rate fields; currency/timezone assumptions remain documented |
| 2.6 | Accept/reject/counter, ceiling, tentative reservation | Atomic call decisions, sticky three-round limit, one agreement, booking-row claim recovery; S5/E6/E8 reruns and E7 follow-up retained | Partial: service checks pass; candidate continuation rollout and human voice regressions remain open |
| 3.1 | Mock handoff to senior rep who confirms | Spoken mocked handoff; App rep Confirm sends once. Historical LD01080 has reference-bearing PENDING | Qualified: PENDING is acknowledgement, not final confirmation; no document-collection workflow is built |
| 3.2 | Log MC, load ID, rate, outcome and notes | Twin call and booking rows, per-row atomic events, reconstructed call and optional close notes. End report handles pre-tool calls when delivered | Partial: no notes are invented for skipped close; current E1/E2 each omit close_call in 3/3 checkpoints; callback delivery not guaranteed. Twin rather than TMS logging is an explicit interpretation, as no TMS logging command exists |
| 3.3 | Unreliable raw TCP handled gracefully | Bounded read retry budget, strict framing and loopback fault servers; booking uses one fresh connection within its total deadline and never retries | Met within recorded contract and injected faults |
| 3.4 | Platform, FMCSA, legacy TMS and mocked rep queue | Native voice, Twin and Apps; service adapters; rep queue and mocked transfer | Met |

## Page 4: additional requirements

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 4.1 | Enforce max_rate; never disclose directly or indirectly | Fresh rate checks and marked-value tests; expected ceiling withheld from agent. Known policy bands/observed offers can still constrain its value | Partial: enforcement implemented; absolute indirect secrecy is not proven. Earlier Qualified versus Partial disagreement is resolved conservatively here, without claiming the risk vanished |
| 4.2 | Code after authority, before matching, with no bypass | Same-call stored authority/code gates; unauthorized state/destination fields refused; adversarial checkpoints and native urgency refusal | Met within demo destination exception |
| 4.3 | All activity in native Twin | Only calls/bookings tables, no second database. Each state and its event share a write; earlier asks and freed-load history retained | Partial: R3 local completion awaiting rollout; speech and undelivered callback/write gaps disclosed |
| 4.4 | HappyRobot Apps operational signals/actions without raw logs | Candidate has carrier/MC, lane, dates, equipment, posted/agreed payment, readable activity, next action, send mode, disabled Confirm and retained receipt recovery | Partial: local build/tests pass; current published Build 17 is older. Platform name and final visual acceptance require approved publication |
| 4.5 | Defined KPIs, standard/edge/adversarial tests, results documented and presented | kpis.md, qa-package.md, qa-results.md, historical checkpoints, seeded tests, nine HTTP journeys and two native full text conversations | Partial: package written; walkthrough presentation not yet recorded. Pressure run idle timeout is retained, not a successful closing |
| 4.6 | Docker and one-command cloud deployment | Dockerfile and make deploy; earlier reviewed versions deployed to Fly | Met: one-time secrets/cloud setup still required, candidate deployment pending approval |

## Page 5: experience, boundaries and security

| # | Requirement | Evidence and candidate state | Status |
|---|---|---|---|
| 5.1 | Direct, efficient, conversational | Version 3 opening/name correction and one clean owner call; Version 4 standard text handoff. Pressure text run stalled for 141 s before idle timeout | Partial: voice greeting/correction/interruptions and refusal-path closure need acceptance; no population efficiency claim |
| 5.2 | Up to three counters, failed close logged, no transfer | Service rounds across loads/MC changes and sticky failure, E6 checkpoint repetitions | Qualified: enforced state and tested checkpoints; human failed-path close remains open |
| 5.3 | Authenticate every endpoint; resist OTP social engineering | Separate agent/ops keys, App verified session, live historical 401 probes and offline route tests; service gate independent of model | Met within PoC scope; shared inbox is not identity proof and cross-call abuse controls are deferred |
| 5.4 | Web call; no phone provisioned | Native web-call deployment | Met |

## Page 5: deliverables

| # | Deliverable | State | Status |
|---|---|---|---|
| D1 | Prospect email with build and next steps | Corrected draft in submission.md, five tailored next steps and links; sending/submission requires approval | Partial: draft ready, owner review/send pending |
| D2 | Business/IT build description | Corrected build-description.md and generated local PDF; explicit identity, capture, ceiling, PENDING and reliability limits | Partial: candidate ready, final owner review pending |
| D3 | Private repository and reviewer invitations | Private/default-main verified read-only on GitHub; only owner collaborator and zero pending invitations | Partial: invitations/access validation pending owner approval |
| D4 | Workflow link | Exact candidate editor and web-call links in submission.md; Version 3 currently live | Qualified: link ready; publish Version 4 only after service deployment approval |
| D5 | About-five-minute video, demo, App and QA | walkthrough.md run sheet and required closing next steps | Gap: owner-recorded video and final URL absent |

## R1 to R6 completion and release boundary

| Item | Local completion | Remaining acceptance or owner action |
|---|---|---|
| R1 conversation correctness | Version 3 fixes retained; Version 4 fixed prompt passes all 22 checkpoints twice (44/44) plus E5 6/6, after earlier 58/66, 39/44 and 43/44 batches. No final booking claim observed | Deploy service, publish Version 4, run exact-version voice checklist; refusal-path closing remains bounded, not proven |
| R2 basic carrier experience | Version 3 greeting/name/MC corrections already implemented, no duplicate rebuild | Human greeting, misheard-MC and interruption regression checks |
| R3 activity capture | Per-event asks/search/pitch/delivery/notes/end coverage and privacy/reconstruction tests complete | Deploy then publish callback; undelivered events and spoken content remain outside guarantees |
| R4 essential dashboard | Redesign pieces 1/2 plus send mode, missing-history labels and recovery regressions complete | App publication, platform name and final visual review; broader cosmetic pieces deferred |
| R5 QA and KPIs | Layers, versions, seeds, counts, failures and definitions documented; actual 100% service coverage | Owner voice checks, recorded presentation; capacity unproven |
| R6 handover | Corrected email, build description, links, reviewer instructions and walkthrough outline | Claude review, owner approvals, video, access and submission |

## Recommended work, not invented submission requirements

X1 full redesign pieces 3 to 7 requires owner review before further expansion. X2 capacity needs an agreed workload for a pilot, not an assumed 12-call rubric. X3 carrier-experience measures need actual audio/turn evidence. X4 a verbatim transcript is not required for the chosen structured-decision trail; adding one would need retention/redaction decisions. Optional A to C are analyzed separately and remain unimplemented without approval.

The page 1 phrase about confirmed bookings and page 3 rep-confirm step are ambiguous; D-22 follows the explicit tentative-reservation process. No official inventory quota, permanent load-consumption guarantee, finalization command or successful live BOOKED response is invented. Luke's Q8 remains open.

## Latest Version 4 checkpoint findings

The owner-requested full 22-case rerun completed 58/66 passes, with 18/22 cases passing all three repetitions. R2 remains open for S6 wrong-name recovery. R3 closing-note coverage is incomplete in E1/E2 despite correct spoken refusal/unavailable responses. S5 has a narrower explicit-load-ID omission, with negotiate, close and truthful handoff observed. E7 and all six adversarial cases passed 3/3. These current results supersede any impression that the earlier 18/18 subset established the entire prompt's behavior. They do not replace the historical failures or prove audio reliability. No prompt change or publication accompanied the rerun. See qa-results.md and the pinned qa-v4 evidence files.
