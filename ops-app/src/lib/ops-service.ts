// Server-only client for the carrier sales ops service. The service is
// authoritative for bookings and rep decisions. This app never writes Twin,
// sends email or books loads.
//
// Only approved fields are projected. Upstream bodies on error are discarded:
// callers receive an HTTP status (or a fixed status label) and nothing else.
import { getOpsEnv } from "@/lib/env";

const OPS_BASE_URL = "https://codex-e2e-lab-sg-20261031.fly.dev";
const TIMEOUT_MS = 10_000;

export type Cohort = "real" | "synthetic";
export type RepDecision = "awaiting" | "confirmed" | "declined";
export type RepAction = "confirm" | "decline" | "reconcile";

export type QueueRow = {
  id: string;
  callId: string | null;
  loadId: string | null;
  mc: string | null;
  rate: number | null;
  state: string | null;
  reference: string | null;
  tmsStatus: string | null;
  repDecision: RepDecision | null;
  rep: string | null;
  reviewRequired: boolean | null;
  reason: string | null;
  cohort: Cohort | null;
  createdAt: string | number | null;
};

export type CallTranscript = {
  transcript: string | null;
  summary: string | null;
  summarySource: string | null;
  notes: string | null;
  sentiment: string | null;
  tools: string[];
  source: string | null;
  complete: boolean | null;
};

export type CallRow = {
  id: string;
  mc: string | null;
  cohort: Cohort | null;
  outcome: string | null;
  rounds: number | null;
  startedAt: string | number | null;
  closedAt: string | number | null;
  codePassedAt: string | number | null;
  carrierName: string | null;
  transcript: CallTranscript | null;
};

export type Kpis = {
  realCalls: number | null;
  codePassedCalls: number | null;
  acknowledgedHandoffs: number | null;
  northstar: number | null;
  tmsConfirmed: number | null;
  repConfirmed: number | null;
  unknown: number | null;
  syntheticCalls: number | null;
  unmetDemand: number | null;
};

export type Snapshot = {
  status: string | null;
  queue: QueueRow[];
  calls: CallRow[];
  kpis: Kpis;
};

/** Failure carries only an HTTP status or a fixed label, never upstream text. */
export type OpsFailure = { status: number | "not_configured" | "no_response" | "invalid_response" };

type Json = Record<string, unknown>;
const obj = (v: unknown): Json => (v && typeof v === "object" && !Array.isArray(v) ? (v as Json) : {});
const str = (v: unknown, max = 200): string | null =>
  typeof v === "string" ? v.slice(0, max) : typeof v === "number" && Number.isFinite(v) ? String(v) : null;
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const bool = (v: unknown): boolean | null => (typeof v === "boolean" ? v : null);
const time = (v: unknown): string | number | null =>
  typeof v === "number" && Number.isFinite(v) ? v : typeof v === "string" ? v.slice(0, 40) : null;
const cohort = (v: unknown): Cohort | null => (v === "real" || v === "synthetic" ? v : null);
const decision = (v: unknown): RepDecision | null =>
  v === "awaiting" || v === "confirmed" || v === "declined" ? v : null;

// Defense in depth for free text: mask verification codes, policy or ceiling
// figures, hashes and token-like strings even if upstream already redacted.
export function redactText(text: string, max = 20_000): string {
  return text
    .slice(0, max)
    // Long tokens and hashes first so later rules cannot split them.
    .replace(/[A-Za-z0-9_-]{40,}/g, "[redacted]")
    .replace(/\b[a-f0-9]{24,}\b/gi, "[redacted]")
    .replace(
      /\b(otp|one[- ]time|code|passcode|pin|verification|token|password|secret)\b([^\n]{0,40}?)(\d(?:[\s-]?\d){3,7})/gi,
      "$1$2[redacted]"
    )
    .replace(
      /\b(ceiling|cap|floor|max(?:imum)? rate|min(?:imum)? rate|target rate|policy)\b([^\n\d$]{0,20})\$?\s?\d[\d,.]*/gi,
      "$1$2[redacted]"
    );
}

function toolNames(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  // Tool arguments and results can carry codes or pricing: names only.
  return v
    .map((t) => (typeof t === "string" ? t : str(obj(t).name, 60)))
    .filter((t): t is string => Boolean(t && /^[A-Za-z0-9_. -]{1,60}$/.test(t)))
    .slice(0, 50);
}

function projectTranscript(v: unknown): CallTranscript | null {
  if (v === null || v === undefined || typeof v !== "object") return null;
  const t = obj(v);
  const text = (x: unknown, max: number) => (typeof x === "string" ? redactText(x, max) : null);
  return {
    transcript: text(t.transcript, 20_000),
    summary: text(t.summary, 2_000),
    summarySource: str(t.summary_source, 60),
    notes: text(t.notes, 2_000),
    sentiment: str(t.sentiment, 40),
    tools: toolNames(t.tools),
    source: str(t.source, 60),
    complete: bool(t.complete),
  };
}

export function projectSnapshot(body: unknown): Snapshot | null {
  const b = obj(body);
  if (!Array.isArray(b.queue) || !Array.isArray(b.calls)) return null;
  const queue: QueueRow[] = b.queue.flatMap((raw) => {
    const r = obj(raw);
    const id = str(r.id, 128);
    if (!id) return [];
    return [{
      id,
      callId: str(r.call_id, 128),
      loadId: str(r.load_id, 64),
      mc: str(r.mc, 32),
      rate: num(r.rate),
      state: str(r.state, 40),
      reference: str(r.reference, 80),
      tmsStatus: str(r.tms_status, 60),
      repDecision: decision(r.rep_decision),
      rep: str(r.rep, 120),
      reviewRequired: bool(r.review_required),
      reason: typeof r.reason === "string" ? redactText(r.reason, 300) : null,
      cohort: cohort(r.cohort),
      createdAt: time(r.created_at),
    }];
  });
  const calls: CallRow[] = b.calls.flatMap((raw) => {
    const c = obj(raw);
    const id = str(c.id, 128);
    if (!id) return [];
    return [{
      id,
      mc: str(c.mc, 32),
      cohort: cohort(c.cohort),
      outcome: str(c.outcome, 60),
      rounds: num(c.rounds),
      startedAt: time(c.started_at),
      closedAt: time(c.closed_at),
      codePassedAt: time(c.code_passed_at),
      carrierName: str(c.carrier_name, 120),
      transcript: projectTranscript(c.transcript),
    }];
  });
  const k = obj(b.kpis);
  return {
    status: str(b.status, 40),
    queue,
    calls,
    kpis: {
      realCalls: num(k.real_calls),
      codePassedCalls: num(k.code_passed_calls),
      acknowledgedHandoffs: num(k.acknowledged_handoffs),
      northstar: num(k.northstar),
      tmsConfirmed: num(k.tms_confirmed),
      repConfirmed: num(k.rep_confirmed),
      unknown: num(k.unknown),
      syntheticCalls: num(k.synthetic_calls),
      unmetDemand: num(k.unmet_demand),
    },
  };
}

/** Actions the app offers for a row. The service remains authoritative. */
// The caller did not explicitly agree to book: Confirm is never offered.
export const CALLER_CONSENT_REVIEW = "caller_confirmation_review";

export function allowedActions(row: Pick<QueueRow, "state" | "repDecision" | "reason">): RepAction[] {
  if (row.repDecision !== "awaiting") return [];
  const consentReview = row.reason?.trim() === CALLER_CONSENT_REVIEW;
  if (row.state === "ACK_PENDING" || row.state === "CONFIRMED") return consentReview ? ["decline"] : ["confirm", "decline"];
  if (row.state === "UNKNOWN") return ["reconcile", "decline"];
  return [];
}

async function opsFetch(path: string, init: RequestInit): Promise<Response | OpsFailure> {
  const { opsApiKey } = getOpsEnv();
  if (!opsApiKey) return { status: "not_configured" };
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${opsApiKey}`);
  headers.set("Accept", "application/json");
  try {
    return await fetch(`${OPS_BASE_URL}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    return { status: "no_response" };
  }
}

export async function getSnapshot(): Promise<{ ok: true; snapshot: Snapshot } | ({ ok: false } & OpsFailure)> {
  const res = await opsFetch("/ops/snapshot", { method: "GET" });
  if (!(res instanceof Response)) return { ok: false, ...res };
  if (!res.ok) {
    await res.body?.cancel().catch(() => {});
    return { ok: false, status: res.status };
  }
  const snapshot = projectSnapshot(await res.json().catch(() => null));
  return snapshot ? { ok: true, snapshot } : { ok: false, status: "invalid_response" };
}

export const BOOKING_ID_RE = /^[A-Za-z0-9_-]{1,128}$/;

export async function postRepAction(
  bookingId: string,
  action: RepAction,
  actor: string
): Promise<{ ok: true; status: number } | ({ ok: false } & OpsFailure)> {
  if (!BOOKING_ID_RE.test(bookingId)) return { ok: false, status: 400 };
  const res = await opsFetch(`/bookings/${encodeURIComponent(bookingId)}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor }),
  });
  if (!(res instanceof Response)) return { ok: false, ...res };
  await res.body?.cancel().catch(() => {});
  return res.ok ? { ok: true, status: res.status } : { ok: false, status: res.status };
}

export function describeFailure(f: OpsFailure): string {
  if (typeof f.status === "number") return `HTTP ${f.status}`;
  return {
    not_configured: "service not configured",
    no_response: "no response",
    invalid_response: "unexpected response",
  }[f.status];
}
