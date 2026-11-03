// Explicit projection of authenticated operations snapshots. Unknown fields stay private.
import { events, type EventRow } from "@/lib/event-history";
import { projectRepLoad } from "@/lib/rep-load";
export type { RepLoad } from "@/lib/rep-load";
import type { RepLoad } from "@/lib/rep-load";
import { redactText } from "@/lib/redact-text";

export type Cohort = "real" | "synthetic";
export type RepAction = "confirm" | "decline" | "reconcile";

export type Booking = {
  carrierName: string | null;
  load: RepLoad | null;
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
  codePassed: boolean;
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
  endsReported: number | null;
  syntheticCalls: number | null;
};

export type Lane = {
  equipment: string | null;
  originState: string | null;
  destState: string | null;
  calls: number;
};

export type Snapshot = {
  liveBooking: boolean | null;
  generatedAt: string | null;
  kpis: Kpis;
  turnedAway: Lane[];
  bookings: Booking[];
  calls: Call[];
};

type Json = Record<string, unknown>;
const obj = (v: unknown): Json =>
  v && typeof v === "object" && !Array.isArray(v) ? (v as Json) : {};
const list = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const str = (v: unknown, max = 200): string | null =>
  typeof v === "string"
    ? v.slice(0, max)
    : typeof v === "number" && Number.isFinite(v)
      ? String(v)
      : null;
const num = (v: unknown): number | null =>
  typeof v === "number" && Number.isFinite(v) ? v : null;
const cohort = (v: unknown): Cohort | null =>
  v === "real" || v === "synthetic" ? v : null;

function projectBooking(raw: unknown): Booking[] {
  const b = obj(raw);
  const loadId = str(b.load_id, 64);
  const version = num(b.version);
  if (!loadId || version === null) return [];
  const send = obj(b.send);
  const history = events(b.events);
  return [
    {
      loadId,
      version,
      carrierName: str(b.carrier_name, 120),
      load: projectRepLoad(b.load),
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
    },
  ];
}

function projectCall(raw: unknown): Call[] {
  const c = obj(raw);
  const id = str(c.id, 128);
  if (!id) return [];
  const booking = obj(c.booking);
  const search = obj(c.search);
  const terms = [search.equipment, search.origin_state, search.dest_state].map(
    (t) => str(t, 32),
  );
  return [
    {
      id,
      cohort: cohort(c.cohort),
      startedAt: str(c.started_at, 40),
      closedAt: str(c.closed_at, 40),
      mc: str(c.mc, 32),
      carrierName: str(c.carrier_name, 120),
      verifiedAt: str(c.verified_at, 40),
      codePassed: c.code_passed === true,
      rounds: num(c.rounds),
      outcome: str(c.outcome, 60),
      bookingState: str(booking.state, 40),
      bookingLoadId: str(booking.load_id, 64),
      agreedRate: num(obj(c.agreement).rate),
      search: terms.some(Boolean)
        ? terms.map((t) => t ?? "any").join(" / ")
        : null,
      summary: typeof c.summary === "string" ? redactText(c.summary) : null,
      events: events(c.events),
    },
  ];
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
    endsReported: num(k.ends_reported),
    syntheticCalls: num(k.synthetic_calls),
  };
}

export function projectSnapshot(body: unknown): Snapshot | null {
  const b = obj(body);
  if (
    b.status !== "ok" ||
    !Array.isArray(b.bookings) ||
    !Array.isArray(b.calls)
  )
    return null;
  return {
    liveBooking: typeof b.live_booking === "boolean" ? b.live_booking : null,
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
