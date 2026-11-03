// Server-only client for the carrier sales service (architecture section 11, D-30).
// The service holds every rule; this app reads its snapshot and forwards a rep's
// actions. It never reads Twin, never talks to the TMS, and never sends email.
//
// Only listed fields are projected, so a field the service adds later stays out of
// the page by default. Upstream error bodies are discarded.
import { getOpsEnv } from "@/lib/env";
import { projectSnapshot, type Booking, type RepAction, type Snapshot } from "@/lib/snapshot";
export { projectSnapshot } from "@/lib/snapshot";
export type { Booking, Call, Cohort, Kpis, Lane, RepAction, Snapshot } from "@/lib/snapshot";
export { redactText } from "@/lib/redact-text";
export type { EventRow } from "@/lib/event-history";

const SNAPSHOT_TIMEOUT_MS = 10_000;
const ACTION_TIMEOUT_MS = 45_000; // a confirm sends once, then saves for up to about 10 seconds
const STALE_SEND_MS = 60_000; // a SUBMITTING row this old lost its sender: offer Reconcile

/** Failure carries only an HTTP status or a fixed label, never upstream text. */
export type OpsFailure = { status: number | "not_configured" | "no_response" | "invalid_response" };

type Json = Record<string, unknown>;
const obj = (v: unknown): Json => v && typeof v === "object" && !Array.isArray(v) ? v as Json : {};
const str = (v: unknown, max = 200): string | null => typeof v === "string" ? v.slice(0, max) : null;
const num = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null;

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
