# Inbound Carrier Sales

An AI voice agent for HappyRobot Logistics (a simulated brokerage). It checks carrier authority, verifies an emailed code, finds freight and negotiates a rate. A senior rep reviews the resulting reservation before any booking is sent to the TMS.

[Operations App](https://carrier-sales-proposal-sg.happyrobot.dev/?view=overview) · [Web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) · [Workflow](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w)

[Watch the walkthrough video](https://youtu.be/2CEQBlY4iys): a working carrier call, the operations dashboard, and quality checks.

## Run locally

Prerequisites: Python 3.12, Make, a running Docker engine with Compose v2, free ports `3080` and `3081`, and internet access for the initial image/package downloads. No cloud credentials or host Node installation are needed.

```bash
make review
```

Open <http://127.0.0.1:3081/enter/rep> if the browser does not open automatically. The App runs on port `3080`. This disposable environment uses the real service with simulated Twin, FMCSA, email and sign-in, plus a loopback TCP TMS. Confirm sends one simulated booking and displays PENDING. It never contacts real carriers or the hosted TMS.

Rerunning recreates the local fixtures. `make review-down` removes this local environment and its volume.

## Follow the workflow

```text
Web call -> AI disclosure -> authority -> email code -> load search
         -> negotiation -> Twin reservation -> senior-rep review -> TMS
```

The model handles conversation; the service controls verification, prices and state. The expected code and rate ceiling stay inside the service. The caller's spoken code passes through the workflow for checking. The handoff is mocked, as the brief permits.

Start at [happyrobot/tool-bindings-v20.json](happyrobot/tool-bindings-v20.json), then [service/api.py](service/api.py). [service/main.py](service/main.py) wires the adapters. `calls.py` handles verification; `selling.py` handles search and negotiation; `rep_actions.py` controls booking. The App enters through [ops-app/src/app/page.tsx](ops-app/src/app/page.tsx), reads service snapshots and forwards authorized rep actions. Twin is the only persistent application datastore.

## Verify

```bash
python3.12 -m venv .venv
. .venv/bin/activate
make install
make check
```

This runs lint, formatting, strict types, tests and coverage/documentation gates without external service calls. `make hooks` enables the same checks on staged files before commits.

For direct App checks, install Node 22:

```bash
cd ops-app
npm ci --include=dev
npm test
npm run lint
NODE_ENV=production npm run build
npm run typecheck
```

Results and test boundaries are in [docs/results.md](docs/results.md).

## External setup and deployment

Hosted operation requires TMS credentials, an FMCSA key, HappyRobot organization/API access, SMTP configuration, service keys and pricing/OTP secrets. Provision Twin with [bootstrap SQL](tools/twin-schema.sql), then configure the native workflow, App and rep sign-in. Verify the selected schema with `python -m tools.check_twin_schema --environment staging`. See [.env.example](.env.example), [onboarding](docs/reference/onboarding.md) and [release instructions](docs/reference/release.md).

With an authenticated Fly CLI, an existing Fly app and configured secrets, `make deploy APP=<fly-app> APP_URL=<native-app-url>` deploys the service and checks authenticated health/TMS reachability. It does not publish the native App or workflow. Always specify the target; `fly.toml` names the rollback service.

## Read next

1. [ARCHITECTURE.md](ARCHITECTURE.md): components, call flow and enforced rules.
2. [docs/decisions.md](docs/decisions.md): negotiation, verification and booking tradeoffs.
3. [docs/results.md](docs/results.md): North Star definitions, standard/edge/adversarial tests and evidence.
4. [docs/build-description.md](docs/build-description.md): business and IT overview.

The [challenge PDF](docs/FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf) defines the requirements; [docs/reference/assignment.md](docs/reference/assignment.md) summarizes them. [docs/tms/README.md](docs/tms/README.md) covers the TCP protocol. AI contributors should read [AGENTS.md](AGENTS.md). Dated material in `docs/history/` and `happyrobot/history/` is not current release guidance.

## Known limits

- The demo inbox proves inbox access, not carrier identity. A pilot needs enrolled carrier contacts.
- Live carrier booking is off. A temporary, MC-scoped challenge-sandbox permission demonstrates hosted Confirm on the same call; [release details](docs/reference/release.md#current-release-state) give its expiry. PENDING is acknowledged, not BOOKED; no sandbox finalization step is known.
- Unrecognized shipment text goes to a rep. The approved vocabulary needs operational ownership.
- Misheard amounts within pricing limits can become reservations; repeated corrections can end a call. Rep review remains necessary.
- Controlled load tests and repeated development callers do not establish production capacity, market conversion or broad voice reliability.
