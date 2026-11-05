import { demoVoiceRunIds } from "@/lib/demo-voice-runs";

// Current work is unified across the service's deployment tags. Old scope bookmarks still resolve.
export const VIEWS = ["reservations", "overview", "bookings", "calls", "demand"] as const;
export type View = (typeof VIEWS)[number];
export const VIEW_TITLE: Record<View, string> = {
  reservations: "Reservations", overview: "Overview", bookings: "Bookings", calls: "Calls", demand: "Demand",
};
type Params = Record<string, string | string[] | undefined>;
const first = (v: string | string[] | undefined) => Array.isArray(v) ? v[0] : v;
export function readView(params: Params): View {
  const asked = first(params.view);
  if (!asked && first(params.group)) return "overview";
  return VIEWS.find(v => v === asked) ?? "reservations";
}
export function viewHref(view: View) {
  return view === "reservations" ? "/" : `/?view=${view}`;
}
export function recordHref(view: "reservations" | "bookings" | "calls", load?: string | null, run?: string | null) {
  const params = new URLSearchParams({ view });
  if (load) params.set("load", load);
  if (run) params.set("run", run);
  return `/?${params}`;
}
export function workspaceFilters(params: Params) {
  const value = (key: string) => first(params[key])?.trim().slice(0, 128) || "";
  return { query: value("q"), status: value("status"), load: value("load"), run: value("run"), bucket: value("bucket"),
    from: value("from"), to: value("to") };
}
export const isRunId = (id: string | null | undefined): id is string =>
  typeof id === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id);
export function platformRun(id: string | null | undefined, provenance?: unknown) {
  if (!isRunId(id)) return null;
  if (provenance && typeof provenance === "object") {
    const native = provenance as Record<string, unknown>;
    const safe = (v: unknown): v is string => typeof v === "string" && /^[A-Za-z0-9_-]{1,80}$/.test(v);
    if (safe(native.workspace) && safe(native.workflow_id))
      return `https://platform.happyrobot.ai/${native.workspace}/workflows/${native.workflow_id}/runs?run_id=${id}`;
  }
  return demoVoiceRunIds.has(id) ? `https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/runs?run_id=${id}` : null;
}
