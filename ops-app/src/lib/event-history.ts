// Explicit projection of structured call and booking history. Private fields are ignored.
import { projectRepLoad, type RepLoad } from "@/lib/rep-load";

export type EventRow = {
  seq: number | null;
  at: string | null;
  action: string | null;
  status: string | null;
  state: string | null;
  rep: string | null;
  reason: string | null;
  load: RepLoad | null;
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

type Json = Record<string, unknown>;
const obj = (v: unknown): Json => (v && typeof v === "object" && !Array.isArray(v) ? v as Json : {});
const list = (v: unknown): unknown[] => Array.isArray(v) ? v : [];
const str = (v: unknown, max = 200): string | null =>
  typeof v === "string" ? v.slice(0, max) : typeof v === "number" && Number.isFinite(v) ? String(v) : null;
const num = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null;

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
    const from = str(load.origin, 100) ?? "not recorded";
    const to = str(load.destination, 100) ?? "not recorded";
    const offer = num(load.offer);
    const details = ["pickup_datetime", "delivery_datetime", "equipment_type", "weight", "commodity_type", "num_of_pieces", "miles", "dimensions", "notes"]
      .flatMap((key) => { const v = str(load[key], 500); return v === null || v === "" ? [] : [`${key} ${v}`]; });
    return id ? [`${id} ${from} to ${to}${offer === null ? "" : ` at ${offer}`}${details.length ? `, ${details.join(", ")}` : ""}`] : [];
  });
  const search = obj(e.search);
  const lane = [search.equipment, search.origin_state, search.dest_state].map((v) => str(v, 32));
  if (lane.some(Boolean)) parts.push(`search ${lane.map((v) => v ?? "any").join(" / ")}`);
  if (pitched.length) parts.push(`pitched ${pitched.slice(0, 3).join("; ")}`);
  return parts.length ? parts.join(", ") : null;
}

export function events(v: unknown): EventRow[] {
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
        load: projectRepLoad(e.load),
        detail: eventDetail(e),
      };
    });
}

