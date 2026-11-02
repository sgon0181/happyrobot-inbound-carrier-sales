# HappyRobot challenge context

Assignment/platform summaries reviewed 2026-10-28; TMS evidence updated 2026-11-02. Summary of the local assignment PDF and official documentation, without prescribing architecture or a technology stack.

Start with [`onboarding.md`](onboarding.md) for access, current external workflow state and setup steps. For TMS implementation, read [`tms/README.md`](tms/README.md): command usage, codes, parsing, visibility rules and known differences between handbook examples and this candidate token. Read [`tms-contract.md`](tms-contract.md) for measured evidence. These are shared context for both coding agents; the runtime voice agent receives only approved tool results.

## Recruiter clarification, 2026-10-30 (Australia/Sydney)

Source: [Luke's reply](https://mail.google.com/mail/u/?authuser=santiagog11999%40gmail.com#all/1a18873af586e52d), recorded in [`questions.md`](questions.md).

- Booking timing, returning-carrier OTP policy, and TMS rate semantics are intentionally ambiguous. Luke asks us to choose and document assumptions, rather than wait for definitive answers. [`decisions.md`](decisions.md) records the current assumptions; they are not recruiter-confirmed technical facts.
- Present the walkthrough to the brokerage's business team, suitable for a business review.
- Creative additions are optional and should provide client value while following the rubric and guide.
- Fly.io is acceptable; any cloud environment works.
- Use web calls and send OTP through an email integration to the candidate's personal email. No real carrier SMS recipient or dedicated phone number is needed for this demo. This destination is demo data, not proof of a real carrier's contact ownership. No specific test MCs were supplied.

## Assignment

Source: [the assignment PDF](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf).

Automate a freight brokerage's inbound carrier calls: collect MC number, verify active FMCSA authority, verify an SMS/email OTP, match available loads by lane and equipment, negotiate, reserve/book, and mock a senior-representative handoff. Log carrier MC, load ID, agreed rate, outcome, and notes.

Mandatory requirements:
- OTP verification during the call before load matching; no social-engineering bypass. Page 4 requires OTP after authority verification, while the earlier process description mentions new carriers.
- Never exceed or disclose `max_rate`, directly or indirectly. Maximum three counter rounds per call; unsuccessful negotiation ends without transfer.
- HappyRobot web call trigger; no dedicated phone number provisioned. Senior-representative transfer is mocked.
- All call activity in Twin; operational signals and actions in HappyRobot Apps, without requiring raw platform logs. External databases/UIs require a native limitation and justification.
- Authentication on all endpoints. Graceful handling of TMS timeouts and malformed responses.
- Defined northstar KPIs, scripted standard/edge-case tests, adversarial tests, documented results.
- Docker containerization and single-command cloud deployment.
- Private repository with reviewer invitations.

Deliverables: prospect summary email, IT/business build description, repository link, HappyRobot workflow link, approximately five-minute walkthrough showing live demo, dashboard, and QA results.

## Provided systems and data

- Candidate portal: workspace access, TMS hostname/port/personal token, FMCSA API key, assignment links, and submission form. Credential values are not reproduced here.
- Legacy TMS: source of load data and booking responses. The handbook's transcripts are examples, not observed live inventory.
- FMCSA API: carrier operating-authority lookup.
- HappyRobot: conversation/workflow execution, tools, Twin storage, Apps interface, and evaluation facilities.

## Relevant platform behavior

- Workflows consist of a trigger and processing/agent nodes. Tools attached to an agent execute child actions during the conversation. [Introduction](https://docs.happyrobot.ai/introduction), [Prompts and tools](https://docs.happyrobot.ai/voice-agents/prompts-and-tools).
- Web call requires an Inbound Voice Agent. Each environment has a deployment URL; enhanced security requires authorized HappyRobot sign-in and is documented as enabled by default. [Triggers](https://docs.happyrobot.ai/workflows/triggers).
- Tool Call Result selects fields exposed to the conversational agent; hidden fields remain available downstream and in run details. Opening the panel is read-only; Sync/Generate executes nodes and can cause real writes/messages. [Tool output visibility](https://docs.happyrobot.ai/tools/tool-call-result).
- Webhook nodes make HTTP requests with configurable authentication. Custom Code runs sandboxed Python with no network access or arbitrary package installation. [HTTP calls](https://docs.happyrobot.ai/core-nodes/webhook), [Custom Code](https://docs.happyrobot.ai/core-nodes/custom-code).
- Twin is organization-scoped PostgreSQL with native read/write nodes, SQL, API, and MCP access. Workflow run dumps capture completed runs only, skipping failed runs. [Twin](https://docs.happyrobot.ai/twin/overview), [Run dumps](https://docs.happyrobot.ai/twin/workflow-run-dumps).
- Apps support a managed GitHub repository, Next.js full-stack template, sandbox editor, local development, and deployment. Twin gateway calls from Apps are documented as server-side calls behind an application authentication check. [Apps](https://docs.happyrobot.ai/apps/overview), [Twin in Apps](https://docs.happyrobot.ai/twin/using-in-apps).
- Native Northstars are behavioral grading criteria. Prompt tests check responses/tool calls; adversarial tests simulate conversations; suites group tests. Full-workflow tests can execute real side effects. [Test suites](https://docs.happyrobot.ai/evaluate/test-suites), [Adversarial tests](https://docs.happyrobot.ai/evaluate/adversarial-tests).

## TMS protocol essentials

[Official protocol and command reference](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/).

- TCP, ASCII, CRLF line endings, one request per connection; documented maximum frame size 4096 bytes including terminator, idle timeout 30 seconds.
- Request: `CMD:<command>|AUTH:<token>|KEY:VALUE...` followed by CRLF. Values cannot contain pipes or CRLF. Response fields are right-space-padded; field order is not guaranteed across builds.
- Success: record lines followed by `END` and CRLF. Error: `ERR|CODE:<code>|MSG:<message>` and CRLF.
- `LOAD_QUERY`: filtered search; `LOAD_GET`: full load record; `LOAD_BOOK`: commit booking; `DEBUG_ECHO`: transport/authentication diagnostic that bypasses fault injection.
- Injected faults include timeouts, partial responses missing `END`, malformed framing, and delayed connection closure.
- `RATE` is posted price; `MAX_BUY` is internal pricing, present only for enabled tokens. Sample posted rates exceed sample `MAX_BUY` values. `LOAD_GET` also returns booked/past-pickup loads.
- Booking state is token-scoped; repeated attempts can return `ALREADY_BOOKED`. Exact rate-validation rules are not fully documented.
- Source discrepancy: PDF describes tentative reservation before senior-rep confirmation; handbook describes `LOAD_BOOK` as committing a booking.
- Luke delegated the booking and rate ambiguities to the candidate on 2026-10-30. Sending `LOAD_BOOK` at the rep's Confirm (D-22) and the provisional `MAX_BUY` mapping (D-10) are documented assumptions, not confirmed TMS capabilities.
- Newer owner-recorded evidence in [`questions.md`, Q8](questions.md) reports booking acknowledgements with `STATUS:PENDING`, rather than the handbook's `BOOKED`. Final confirmation behavior is unresolved. The contract now records the bounded live experiments and sanitized fixtures; D-22 reserves at rate agreement, sends at the rep's Confirm, and shows the actual TMS status. No finalization operation is invented.
