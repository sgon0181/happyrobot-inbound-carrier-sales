// Server-only client for the carrier sales service (architecture section 11, D-30).
// The service holds every rule; this app reads its snapshot and forwards a rep's
// actions. It never reads Twin, never talks to the TMS, and never sends email.
//
// Only listed fields are projected, so a field the service adds later stays out of
// the page by default. Upstream error bodies are discarded.
import { getOpsEnv } from "@/lib/env";

const SNAPSHOT_TIMEOUT_MS = 10_000;
const ACTION_TIMEOUT_MS = 45_000; // a confirm sends once, then saves for up to about 10 seconds
const STALE_SEND_MS = 60_000; // a SUBMITTING row this old lost its sender: offer Reconcile

export type Cohort = "real" | "synthetic";
export type RepAction = "confirm" | "decline" | "reconcile";

export type EventRow = {
  seq: number | null;
  at: string | null;
  action: string | null;
  status: string | null;
  state: string | null;
  rep: string | null;
  reason: string | null;
  detail: string | null; // the business fields: MC, load, rate, offers, round, TMS answer
};

// Event fields an operator needs to reconstruct a call or a booking, by label.
const EVENT_DETAIL: [string, string][] = [
  ["mc", "MC"],
  ["heard", "carrier said"],
  ["ask", "ask"],
  ["call_id", "call"],
  ["load_id", "load"],
  ["rate", "rate"],
  ["offer", "offer"],
  ["round", "round"],
  ["tries_left", "tries left"],
  ["reference", "ref"],
  ["tms_status", "TMS"],
  ["load_status", "TMS load"],
  ["ended_by", "ended by"],
  ["duration_seconds", "seconds"],
];

export type Booking = {
  loadId: string;
  version: number;
  state: string | null;
  callId: string | null;
  mc: string | null;
  rate: number | null;
  cohort: Cohort | null;
  rep: string | null;
  reference: string | null;
  tmsStatus: string | null;
  reason: string | null;
  sendStep: string | null;
  sendError: string | null;
  sendBytes: number | null;
  sendSha256: string | null;
  updatedAt: string | null;
  events: EventRow[];
};

export type Call = {
  id: string;
  cohort: Cohort | null;
  startedAt: string | null;
  closedAt: string | null;
  mc: string | null;
  carrierName: string | null;
  verifiedAt: string | null;
  rounds: number | null;
  outcome: string | null;
  bookingState: string | null;
  bookingLoadId: string | null;
  agreedRate: number | null;
  search: string | null;
  summary: string | null;
  events: EventRow[];
};

export type Kpis = {
  calls: number | null;
  codePassed: number | null;
  handoffs: number | null;
  northstar: number | null;
  repConfirmed: number | null;
  tmsAcknowledged: number | null;
  tmsConfirmed: number | null;
  unknown: number | null;
  outcomes: Record<string, number>;
  medianSecondsToFirstOffer: number | null;
  closedWithSummary: number | null;
  syntheticCalls: number | null;
};

export type Lane = { equipment: string | null; originState: string | null; destState: string | null; calls: number };

export type Snapshot = {
  generatedAt: string | null;
  kpis: Kpis;
  turnedAway: Lane[];
  bookings: Booking[];
  calls: Call[];
};

/** Failure carries only an HTTP status or a fixed label, never upstream text. */
export type OpsFailure = { status: number | "not_configured" | "no_response" | "invalid_response" };

type Json = Record<string, unknown>;
const obj = (v: unknown): Json => (v && typeof v === "object" && !Array.isArray(v) ? (v as Json) : {});
const list = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const str = (v: unknown, max = 200): string | null =>
  typeof v === "string" ? v.slice(0, max) : typeof v === "number" && Number.isFinite(v) ? String(v) : null;
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const cohort = (v: unknown): Cohort | null => (v === "real" || v === "synthetic" ? v : null);

// Defense in depth for free text written during a call: mask anything that looks like
// a code, a pricing figure or a token, even though the service never stores one.
export function redactText(text: string, max = 2_000): string {
  return text
    .slice(0, max)
    .replace(/[A-Za-z0-9_-]{40,}/g, "[redacted]")
    .replace(
      /\b(otp|one[- ]time|code|passcode|pin|verification|token|password|secret)\b([^\n]{0,40}?)(\d(?:[\s-]?\d){3,7})/gi,
      "$1$2[redacted]"
    )
    .replace(
      /\b(ceiling|cap|max(?:imum)? rate|max buy|target rate|policy)\b([^\n\d$]{0,20})\$?\s?\d[\d,.]*/gi,
      "$1$2[redacted]"
    );
}

function eventDetail(e: Json): string | null {
  const parts = EVENT_DETAIL.flatMap(([key, label]) => {
    const value = str(e[key], 80);
    return value === null ? [] : [`${label} ${value}`];
  });
  const offers = Object.entries(obj(e.offers)).flatMap(([load, offer]) => {
    const amount = num(offer);
    return /^[A-Za-z0-9_-]{1,32}$/.test(load) && amount !== null ? [`${load} ${amount}`] : [];
  });
  if (offers.length) parts.push(`offers ${offers.join(", ")}`);
  // What was pitched: each load's lane and our offer, from the search's own event.
  const pitched = list(e.loads).flatMap((raw) => {
    const load = obj(raw);
    const id = str(load.load_id, 32);
    const from = [str(obj(load.origin).city, 40), str(obj(load.origin).state, 4)].filter(Boolean).join(" ");
    const to = [str(obj(load.destination).city, 40), str(obj(load.destination).state, 4)].filter(Boolean).join(" ");
    const offer = num(load.offer);
    return id ? [`${id} ${from} to ${to}${offer === null ? "" : ` at ${offer}`}`] : [];
  });
  if (pitched.length) parts.push(`pitched ${pitched.slice(0, 3).join("; ")}`);
  return parts.length ? parts.join(", ") : null;
}

function events(v: unknown): EventRow[] {
  return list(v)
    .slice(-100)
    .map((raw) => {
      const e = obj(raw);
      return {
        seq: num(e.seq),
        at: str(e.at, 40),
        action: str(e.action, 60),
        status: str(e.status, 60),
        state: str(e.state, 40),
        rep: str(e.rep, 200),
        reason: str(e.reason, 80),
        detail: eventDetail(e),
      };
    });
}

function projectBooking(raw: unknown): Booking[] {
  const b = obj(raw);
  const loadId = str(b.load_id, 64);
  const version = num(b.version);
  if (!loadId || version === null) return [];
  const send = obj(b.send);
  const history = events(b.events);
  return [{
    loadId,
    version,
    state: str(b.state, 40),
    callId: str(b.call_id, 128),
    mc: str(b.mc, 32),
    rate: num(b.rate),
    cohort: cohort(b.cohort),
    rep: str(b.rep, 200),
    reference: str(b.reference, 80),
    tmsStatus: str(b.tms_status, 40),
    reason: str(b.reason, 80),
    sendStep: str(send.step, 20),
    sendError: str(send.error, 60),
    sendBytes: num(send.bytes),
    sendSha256: str(send.sha256, 64),
    updatedAt: history.at(-1)?.at ?? null,
    events: history,
  }];
}

function projectCall(raw: unknown): Call[] {
  const c = obj(raw);
  const id = str(c.id, 128);
  if (!id) return [];
  const booking = obj(c.booking);
  const search = obj(c.search);
  const terms = [search.equipment, search.origin_state, search.dest_state].map((t) => str(t, 32));
  return [{
    id,
    cohort: cohort(c.cohort),
    startedAt: str(c.started_at, 40),
    closedAt: str(c.closed_at, 40),
    mc: str(c.mc, 32),
    carrierName: str(c.carrier_name, 120),
    verifiedAt: str(c.verified_at, 40),
    rounds: num(c.rounds),
    outcome: str(c.outcome, 60),
    bookingState: str(booking.state, 40),
    bookingLoadId: str(booking.load_id, 64),
    agreedRate: num(obj(c.agreement).rate),
    search: terms.some(Boolean) ? terms.map((t) => t ?? "any").join(" / ") : null,
    summary: typeof c.summary === "string" ? redactText(c.summary) : null,
    events: events(c.events),
  }];
}

function projectKpis(v: unknown): Kpis {
  const k = obj(v);
  const outcomes: Record<string, number> = {};
  for (const [name, count] of Object.entries(obj(k.outcomes))) {
    const n = num(count);
    if (n !== null && /^[a-z_]{1,60}$/.test(name)) outcomes[name] = n;
  }
  return {
    calls: num(k.calls),
    codePassed: num(k.code_passed),
    handoffs: num(k.handoffs),
    northstar: num(k.northstar),
    repConfirmed: num(k.rep_confirmed),
    tmsAcknowledged: num(k.tms_acknowledged),
    tmsConfirmed: num(k.tms_confirmed),
    unknown: num(k.unknown),
    outcomes,
    medianSecondsToFirstOffer: num(k.median_seconds_to_first_offer),
    closedWithSummary: num(k.closed_with_summary),
    syntheticCalls: num(k.synthetic_calls),
  };
}

export function projectSnapshot(body: unknown): Snapshot | null {
  const b = obj(body);
  if (b.status !== "ok" || !Array.isArray(b.bookings) || !Array.isArray(b.calls)) return null;
  return {
    generatedAt: str(b.generated_at, 40),
    kpis: projectKpis(b.kpis),
    turnedAway: list(b.turned_away).map((raw) => {
      const lane = obj(raw);
      return {
        equipment: str(lane.equipment, 32),
        originState: str(lane.origin_state, 8),
        destState: str(lane.dest_state, 8),
        calls: num(lane.calls) ?? 0,
      };
    }),
    bookings: b.bookings.flatMap(projectBooking),
    calls: b.calls.flatMap(projectCall),
  };
}

/** What the page offers for a booking. The service checks again and has the last word. */
export function allowedActions(booking: Pick<Booking, "state" | "updatedAt">, now: number): RepAction[] {
  if (booking.state === "RESERVED") return ["confirm", "decline"];
  if (booking.state === "ACK_PENDING" || booking.state === "UNKNOWN") return ["reconcile"];
  if (booking.state === "SUBMITTING") {
    const since = booking.updatedAt ? Date.parse(booking.updatedAt) : Number.NaN;
    return Number.isNaN(since) || now - since >= STALE_SEND_MS ? ["reconcile"] : [];
  }
  return [];
}

async function opsFetch(path: string, init: RequestInit, timeoutMs: number): Promise<Response | OpsFailure> {
  const { opsApiKey, serviceUrl } = getOpsEnv();
  if (!opsApiKey || !serviceUrl) return { status: "not_configured" };
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${opsApiKey}`);
  headers.set("Accept", "application/json");
  try {
    return await fetch(`${serviceUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch {
    return { status: "no_response" };
  }
}

export async function getSnapshot(): Promise<{ ok: true; snapshot: Snapshot } | ({ ok: false } & OpsFailure)> {
  const res = await opsFetch("/ops/snapshot", { method: "GET" }, SNAPSHOT_TIMEOUT_MS);
  if (!(res instanceof Response)) return { ok: false, ...res };
  if (!res.ok) {
    await res.body?.cancel().catch(() => {});
    return { ok: false, status: res.status };
  }
  const snapshot = projectSnapshot(await res.json().catch(() => null));
  return snapshot ? { ok: true, snapshot } : { ok: false, status: "invalid_response" };
}

export const LOAD_ID_RE = /^[A-Za-z0-9_-]{1,32}$/;

/** The service's answer to a rep action, reduced to the fields the rep is shown. */
export type ActionReply = {
  status: string;
  state: string | null;
  reason: string | null;
  reference: string | null;
  tmsStatus: string | null;
  loadStatus: string | null;
  sendStep: string | null;
  sendError: string | null;
  sendBytes: number | null;
  sendSha256: string | null;
  rawReply: string | null; // every byte the TMS sent, as latin-1 text, kept whole
};

const MAX_RAW_REPLY = 300_000; // above the service's own 256 KiB bound on a reply

export async function postRepAction(
  loadId: string,
  action: RepAction,
  version: number,
  rep: string
): Promise<{ ok: true; reply: ActionReply } | ({ ok: false } & OpsFailure)> {
  if (!LOAD_ID_RE.test(loadId)) return { ok: false, status: 400 };
  const res = await opsFetch(
    `/bookings/${encodeURIComponent(loadId)}/${action}`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ version, rep }) },
    ACTION_TIMEOUT_MS
  );
  if (!(res instanceof Response)) return { ok: false, ...res };
  if (!res.ok) {
    await res.body?.cancel().catch(() => {});
    return { ok: false, status: res.status };
  }
  const body = obj(await res.json().catch(() => null));
  const status = str(body.status, 40);
  if (!status) return { ok: false, status: "invalid_response" };
  return {
    ok: true,
    reply: {
      status,
      state: str(body.state, 40),
      reason: str(body.reason, 80),
      reference: str(body.reference, 80),
      tmsStatus: str(body.tms_status, 40),
      loadStatus: str(body.load_status, 40),
      sendStep: str(obj(body.send).step, 20),
      sendError: str(obj(body.send).error, 60),
      sendBytes: num(obj(body.send).bytes),
      sendSha256: str(obj(body.send).sha256, 64),
      rawReply: str(body.raw_reply, MAX_RAW_REPLY),
    },
  };
}

export function describeFailure(f: OpsFailure): string {
  if (typeof f.status === "number") return `HTTP ${f.status}`;
  return {
    not_configured: "service not configured",
    no_response: "no response",
    invalid_response: "unexpected response",
  }[f.status];
}
