// The same allowlist projects current and historical reservation terms.
import { redactText } from "@/lib/redact-text";

export type RepLoad = {
  origin: string | null;
  destination: string | null;
  pickup: string | null;
  delivery: string | null;
  equipment: string | null;
  postedRate: number | null;
  weight: number | null;
  pieces: number | null;
  miles: number | null;
  commodity: string | null;
  dimensions: string | null;
  notes: string | null;
};

type Json = Record<string, unknown>;
const obj = (v: unknown): Json => v && typeof v === "object" && !Array.isArray(v) ? v as Json : {};
const str = (v: unknown, max = 200): string | null => typeof v === "string" ? v.slice(0, max) : typeof v === "number" && Number.isFinite(v) ? String(v) : null;
const num = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null;

export function projectRepLoad(v: unknown): RepLoad | null {
  if (!v || typeof v !== "object" || Array.isArray(v)) return null;
  const l = obj(v);
  const place = (p: unknown) => {
    const location = [str(obj(p).city, 100), str(obj(p).state, 4)].filter(Boolean).join(", ");
    const zip = str(obj(p).zip, 5);
    return [location, zip && /^[0-9]{5}$/.test(zip) ? zip : ""].filter(Boolean).join(" ") || null;
  };
  return {
    origin: place(l.origin),
    destination: place(l.destination),
    pickup: str(l.pickup_datetime, 40),
    delivery: str(l.delivery_datetime, 40),
    equipment: str(l.equipment_type, 40),
    postedRate: num(l.loadboard_rate),
    weight: num(l.weight),
    pieces: num(l.num_of_pieces),
    miles: num(l.miles),
    commodity: str(l.commodity_type, 120),
    dimensions: str(l.dimensions, 100),
    notes: typeof l.notes === "string" ? redactText(l.notes) : null,
  };
}

