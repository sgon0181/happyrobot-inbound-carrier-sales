// Measure calls, not repeated tool invocations. Keep the complete event history for these measures.
type Json = Record<string, unknown>;
const row = (x: unknown): Json => x && typeof x === "object" && !Array.isArray(x) ? x as Json : {};

function laneKey(raw: unknown): string | null {
  const terms = row(raw);
  const cells = [terms.equipment, terms.origin_state, terms.dest_state];
  if (!cells.some(v => typeof v === "string" && v.length)) return null;
  return cells.map(v => typeof v === "string" ? v.slice(0, 32) : "any").join(" / ");
}

export function callMilestones(history: unknown, lastSearch?: unknown) {
  const events = (Array.isArray(history) ? history : []).map(row);
  const has = (action: string, status?: string) =>
    events.some((e) => e.action === action && (status === undefined || e.status === status));
  const searches = events.filter(e => e.action === "find_loads");
  const empty = searches.filter(e => e.status === "no_match").at(-1);
  const noMatchLane = empty ? laneKey(empty.search) ?? (searches.length === 1 ? laneKey(lastSearch) : null) : null;
  const counters = new Set<number>();
  const offeredIds = new Set<string>();
  const offeredLanes = new Set<string>();
  let missingRound = false;
  for (const e of events) {
    if (e.action === "negotiate" && (e.status === "counter" || e.status === "final_offer")) {
      if (Number.isInteger(e.round) && Number(e.round) > 0) counters.add(Number(e.round));
      else missingRound = true;
    }
    if (e.action === "find_loads" && e.status === "found") {
      const loadRows = Array.isArray(e.loads) ? e.loads.map(row) : [];
      const loads = loadRows.map(l => l.load_id);
      for (const load of loadRows) {
        const terms = [load.origin, load.destination].filter((s): s is string => typeof s === "string");
        if (terms.length) offeredLanes.add(terms.join(" to ").slice(0, 240));
      }
      for (const id of [...loads, ...Object.keys(row(e.offers))]) {
        if (typeof id === "string" && /^[A-Za-z0-9_-]{1,64}$/.test(id)) offeredIds.add(id);
      }
    }
  }
  return {
    authorityAttempted: has("verify_carrier"), authorityPassed: has("verify_carrier", "eligible"),
    codeIssued: has("send_code", "code_issued"), searchAttempted: has("find_loads"),
    noMatchSeen: Boolean(empty), noMatchLane, negotiated: has("negotiate"),
    finalLimit: has("negotiate", "final_offer") && has("negotiate", "negotiation_failed"),
    counters: missingRound || !events.length ? null : counters.size, offeredIds: [...offeredIds], offeredLanes: [...offeredLanes],
  };
}
