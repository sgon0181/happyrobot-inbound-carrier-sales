# Architecture: HappyRobot Inbound Carrier Sales POC

## Context

HappyRobot Logistics wants an AI voice agent to take the first leg of inbound carrier calls:
MC lookup → FMCSA authority → OTP → load match → negotiate (≤3 rounds, never exceed or leak
`max_rate`) → tentative reservation → mocked senior-rep handoff → structured log. Source of
requirements: `FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf`; summary in `PROJECT_GUIDE.md`.

The project folder has no code yet. `REFERENCES/happyrobot-mcp-us-workflows.mcpb` is a thin
`mcp-remote` proxy to `https://mcp.platform.happyrobot.ai/workflows/mcp` (manage workflows,
integrations, testing). Installed in Claude, it lets us build and test the workflow in the
user's workspace directly instead of by hand. `REFERENCES/Lesson4/5.ipynb` are LiveKit course
notebooks, not relevant to the HappyRobot build.

Decisions made: **Python + FastAPI** bridge, **Fly.io** deploy, **hold-then-book** (LOAD_BOOK
only after the mocked senior rep confirms).

## Core design principle

The LLM talks; deterministic code decides. Anything with a compliance rule (OTP, rate ceiling,
round limit, booking) is enforced in the bridge, never in the prompt. The agent only ever
sees what it may say out loud; `max_rate`, OTP codes and raw TMS frames never reach it.

## Components

```
Carrier (web call)
   │
HappyRobot workflow ── Inbound Voice Agent + tools ──HTTPS + API key──► Bridge (FastAPI, Fly.io)
   │   │                                                                  ├─ TCP ──► Legacy TMS
   │   └─ SMS/email node (sends OTP from hidden tool field)                ├─ HTTPS ─► FMCSA QCMobile
   │                                                                      └─ Twin API (state + events)
   └─ post-call: extract/classify → Twin write
Twin (Postgres) ◄────── HappyRobot App (Next.js dashboard, server-side Twin gateway)
                            └─ "Senior rep queue" action ──API key──► Bridge /holds/{id}/confirm → LOAD_BOOK
```

### 1. Bridge service (`bridge/`, Python 3.12, FastAPI, httpx, pydantic)
Stateless compute; all state lives in Twin so no external DB is needed.

| Endpoint | What it enforces |
|---|---|
| `POST /carriers/verify` | MC → FMCSA QCMobile; returns `eligible`, legal name, reason. Normalizes "MC 123" etc. |
| `POST /otp/send` | Only if call already passed FMCSA. Generates 6-digit code, stores **hash** + expiry (5 min) in Twin, sends to the **contact on file** (Twin carrier registry, seeded; never a number the caller dictates). Returns code only in a hidden field for the SMS/email node. Rate-limited (2 sends/call). |
| `POST /otp/verify` | Max 3 attempts, constant-time compare, marks call `otp_verified`. Hard fail ends the call. |
| `POST /loads/search` | Requires `otp_verified` for the call_id. LOAD_QUERY by lane/equipment, drops held/booked/past-pickup loads, returns pitch fields only (no `MAX_BUY`). Ranks top 1–3. |
| `POST /negotiate` | Input: call_id, load_id, carrier ask. Server tracks round (1–3), computes response from `max_rate` with a concession schedule that never lands predictably on the ceiling; returns `accept` / `counter <price>` / `final_reject`. Round 4 is impossible. |
| `POST /holds` | Creates tentative hold in Twin at agreed rate (only a rate the negotiator accepted). |
| `POST /holds/{id}/confirm` · `/release` | Called from the App by the "senior rep"; confirm → LOAD_BOOK (idempotent). |
| `GET /health`, `POST /debug/echo` | Liveness + TMS DEBUG_ECHO diagnostic. |

All routes require `Authorization: Bearer <key>` (separate keys for HappyRobot and the App);
`/health` exempt. Every call writes a `call_events` row to Twin (tool, latency, outcome).

**TMS client (`bridge/tms/`)** – the riskiest piece, built and tested first:
- One TCP connection per request; connect timeout 3 s, total read deadline ~6 s; reject frames
  > 4096 bytes; read until `END\r\n` or `ERR|...`.
- Parser tolerant of right-padding, arbitrary field order, unknown fields; partial (no `END`),
  garbled or wrong-shaped responses → typed `TmsMalformed`, never a crash.
- Reads (QUERY/GET) retry up to 2× with jittered backoff inside the voice latency budget;
  short-lived cache (~60 s) of last good query per lane as a fallback.
- LOAD_BOOK never retried blindly: on timeout, LOAD_GET to check state, then retry once;
  `ALREADY_BOOKED` on our own hold = success.
- Simple circuit breaker; the agent gets `{"status":"tms_unavailable"}` and says so politely
  instead of inventing loads.

### 2. HappyRobot workflow (built via the MCP bundle; exported to `happyrobot/` for version control)
- Web call trigger → Inbound Voice Agent. Prompt: direct, short turns, state machine
  (identify → verify → OTP → match → negotiate → hold → handoff), refuses OTP bypass and any
  rate-ceiling talk. Tools = Webhook nodes to bridge endpoints; Tool Call Result exposes only
  speakable fields.
- OTP send tool's hidden `code` field → native SMS (or email) node.
- Mocked transfer: agent announces handoff; workflow branch marks hold `pending_rep`.
- Post-call: AI extract (MC, load_id, agreed rate, outcome enum, notes, sentiment) → Twin write
  to `calls`. Outcomes: `booked_pending_rep`, `negotiation_failed`, `no_match`,
  `fmcsa_ineligible`, `otp_failed`, `tms_unavailable`, `abandoned`.

### 3. Twin schema
`carriers` (mc, dot, name, phone/email on file, first_seen) · `calls` (call_id, mc, outcome,
load_id, loadboard_rate, agreed_rate, rounds, duration, sentiment, notes) · `call_events`
(per tool call) · `negotiation_rounds` · `otp_challenges` (hash, expiry, attempts) · `holds`
(load_id, call_id, rate, status, rep decision, tms_booking_ref). Seed one demo carrier with the
user's own phone/email so the live demo receives the OTP.

### 4. HappyRobot App (Next.js template, managed repo)
Ops-manager dashboard: KPI tiles, outcome funnel, rate vs. loadboard chart, TMS health/error
rate, recent calls with summary + notes, **Senior rep queue** (confirm/release holds → bridge),
failed-booking retry. Server-side Twin gateway behind App auth; no raw platform logs.

## Northstar KPIs
- Primary: **booked-per-qualified-call** (holds confirmed ÷ calls that passed OTP).
- Guardrails (must be 0): rate-ceiling breaches, `max_rate` disclosures, OTP bypasses,
  >3 counter rounds.
- Health: margin retained (`max_rate − agreed`) / loadboard, avg handle time, TMS
  graceful-failure rate, FMCSA/OTP pass rates.
- Platform Northstars (behavioral): "never discloses ceiling", "OTP before any load detail",
  "≤3 counters then professional close", "concise, carrier-friendly".

## QA
- `bridge/tests/`: pytest unit tests for parser + negotiator + OTP; integration tests against
  `bridge/tests/fake_tms.py`, a local TCP server injecting timeouts, missing `END`, malformed
  frames, slow close, oversized frames. Property test: negotiator never returns > max_rate.
- HappyRobot test suites: standard (happy path, no match, ineligible MC, lane change),
  edge (TMS down mid-call, OTP expiry, wrong code ×3, already booked), adversarial (OTP bypass
  via urgency/authority/"dispatcher already verified", ceiling extraction via "what's your max",
  binary search on offers, prompt injection, wanting a different callback number).
- Results recorded in `docs/qa-results.md` and shown in the App.

## Repo layout (private GitHub repo)
```
bridge/        app/, tms/, fmcsa.py, otp.py, negotiation.py, twin.py, auth.py, tests/
happyrobot/    workflow export, prompts, test-suite definitions
docs/          build-description.md, kpis.md, qa-results.md, summary-email.md, demo-script.md
Dockerfile, docker-compose.yml (bridge + fake TMS), fly.toml, Makefile (`make deploy` = fly deploy)
```
The Apps dashboard lives in HappyRobot's managed repo; linked from the README.

## Build order
1. Install the HappyRobot MCP bundle (user: open the `.mcpb` in Claude desktop and sign in).
   Check our TMS token with DEBUG_ECHO + one LOAD_QUERY to confirm `MAX_BUY` is returned
   (if not, the ceiling source must be decided before step 3).
2. TMS client + fake TMS + tests.
3. Bridge endpoints, Twin client, auth; docker-compose locally.
4. Fly deploy; secrets via `fly secrets`.
5. Workflow + prompts + SMS node; live web-call test.
6. Twin post-call writes; Apps dashboard + rep queue.
7. Test suites, Northstars, QA results; docs, email, demo video.

## Verification
- `make test` (pytest incl. fault-injection suite) green.
- `docker compose up` → curl each endpoint with/without key (401 without).
- After `make deploy`: `/health` OK, DEBUG_ECHO through Fly reaches the TMS.
- Live web call end to end: OTP arrives on demo phone, load pitched, 3-round negotiation,
  hold appears in the App queue, confirm → TMS shows booked; Twin `calls` row correct.
- Run all HappyRobot suites; guardrail KPIs at 0.

## Open items to confirm during step 1
- `MAX_BUY` availability for our token, and the fact that sample posted rates exceed it
  (opening offer will sit below `max_rate`, not at loadboard rate).
- Whether FMCSA returns a usable phone/email for carriers not in the registry; if not, unknown
  carriers get email OTP to the FMCSA-listed address or are routed to a human.
- Exact Twin API auth from an external service (fallback: bridge writes events via a HappyRobot
  webhook-trigger workflow).
