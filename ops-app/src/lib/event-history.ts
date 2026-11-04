// Explicit projection of structured call and booking history. Private fields are ignored.
import { projectRepLoad, type RepLoad } from "@/lib/rep-load";
import { fmtCount, fmtShort, fmtUsd, label } from "@/lib/format";
import { redactText } from "@/lib/redact-text";

export type EventRow = {
  seq: number | null;
  at: string | null;
  action: string | null;
  status: string | null;
  state: string | null;
  rep: string | null;
  callId: string | null;
  reason: string | null;
  load: RepLoad | null;
  detail: string | null; // the business fields: MC, load, rate, offers, round, TMS answer
};

// Event fields an operator needs to reconstruct a call or a booking, by label.
const EVENT_DETAIL: [string, string][] = [
  ["mc", "MC"],
  ["heard", "Carrier said"],
  ["ask", "Amount checked"],
  ["load_id", "Load"],
  ["rate", "Agreed payment"],
  ["offer", "Our offer"],
  ["round", "Counter round"],
  ["tries_left", "Attempts remaining"],
  ["reference", "Reference"],
  ["tms_status", "TMS"],
  ["load_status", "TMS load"],
  ["ended_by", "Call ended by"],
  ["duration_seconds", "Duration in seconds"],
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
    const amount = ["ask", "rate", "offer"].includes(key) ? num(e[key]) : null;
    return value === null ? [] : [`${label}: ${amount === null ? redactText(value) : fmtUsd(amount)}`];
  });
  const offers = Object.entries(obj(e.offers)).flatMap(([load, offer]) => {
    const amount = num(offer);
    return /^[A-Za-z0-9_-]{1,32}$/.test(load) && amount !== null ? [`${load}: ${fmtUsd(amount)}`] : [];
  });
  if (offers.length) parts.push(`Offers: ${offers.join(", ")}`);
  // What was pitched: each load's lane and our offer, from the search's own event.
  const pitched = list(e.loads).slice(0, 3).flatMap(pitchDetail);
  const search = obj(e.search);
  const lane = [search.equipment, search.origin_state, search.dest_state].map((v) => str(v, 32));
  if (lane.some(Boolean)) parts.push(`Requested lane: ${label(lane[0] ?? "any")}, ${lane[1] ?? "anywhere"} to ${lane[2] ?? "anywhere"}`);
  if (pitched.length) parts.push(`Loads offered: ${pitched.join("; ")}`);
  return parts.length ? parts.join(". ") : null;
}

function pitchDetail(raw: unknown): string[] {
  const l = obj(raw);
  const id = str(l.load_id, 32);
  if (!id) return [];
  const details = [
    `${id}: ${str(l.origin, 100) || "not recorded"} to ${str(l.destination, 100) || "not recorded"}`,
    `Offer: ${fmtUsd(num(l.offer))}`,
    `Pickup: ${fmtShort(str(l.pickup_datetime, 40))}`,
    `Delivery: ${fmtShort(str(l.delivery_datetime, 40))}`,
    `Equipment: ${label(str(l.equipment_type, 40))}`,
    `Weight: ${fmtCount(num(l.weight))} lbs`,
    `Pieces: ${fmtCount(num(l.num_of_pieces))}`,
    `Miles: ${fmtCount(num(l.miles))}`,
    `Commodity: ${str(l.commodity_type, 120) || "Not recorded"}`,
    `Dimensions: ${str(l.dimensions, 100) || "Not recorded"}`,
    `Notes: ${redactText(str(l.notes, 500) || "Not recorded")}`,
  ];
  return [details.join(". ")];
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
        callId: str(e.call_id, 128),
        reason: str(e.reason, 80),
        load: projectRepLoad(e.load),
        detail: eventDetail(e),
      };
    });
}

