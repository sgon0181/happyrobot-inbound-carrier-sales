// Keep arithmetic inputs separate from the display timeline, which shows only its latest 100 events.
type Json = Record<string, unknown>;
const record = (v: unknown): Json =>
  v !== null && typeof v === "object" && !Array.isArray(v) ? v as Json : {};
const validRate = (v: unknown): number | null =>
  typeof v === "number" && Number.isFinite(v) && v > 0 ? v : null;

function openingOn(event: Json, loadId: string): number | null | undefined {
  // Undefined means this load was absent. A missing price on its first appearance stays unknown.
  for (const raw of Array.isArray(event.loads) ? event.loads : []) {
    const load = record(raw);
    if (load.load_id === loadId) return validRate(load.offer);
  }
  const legacy = record(event.offers);
  return Object.hasOwn(legacy, loadId) ? validRate(legacy[loadId]) : undefined;
}

export function callPricing(history: unknown, reservationId: string | null, agreement: unknown) {
  const found = (Array.isArray(history) ? history : []).map(record)
    .filter((e) => e.action === "find_loads" && e.status === "found");
  let openingRate = null;
  const agreed = record(agreement);
  if (reservationId && agreed.load_id === reservationId && validRate(agreed.rate) !== null) {
    for (const event of found) {
      const opening = openingOn(event, reservationId);
      if (opening !== undefined) {
        openingRate = opening;
        break;
      }
    }
  }
  return { foundMatch: found.length > 0, openingRate };
}
