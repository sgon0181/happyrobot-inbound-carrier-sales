// Which page of the dashboard is shown, and for which calls. Both live in the URL.
export const VIEWS = ["overview", "activity", "reservations", "bookings", "calls", "demand"] as const;
export type View = (typeof VIEWS)[number];
export type Scope = "real" | "test";

export const VIEW_TITLE: Record<View, string> = {
  overview: "Overview",
  activity: "Desk activity",
  reservations: "Awaiting rep",
  bookings: "Bookings",
  calls: "Calls",
  demand: "Demand",
};

type Params = Record<string, string | string[] | undefined>;
const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

export function readView(params: Params): { view: View; scope: Scope } {
  const asked = first(params.view);
  const view = VIEWS.find((v) => v === asked) ?? "overview";
  return { view, scope: first(params.scope) === "test" ? "test" : "real" };
}

export function viewHref(view: View, scope: Scope): string {
  const query = new URLSearchParams();
  if (view !== "overview") query.set("view", view);
  if (view !== "overview" && scope === "test") query.set("scope", "test");
  const text = query.toString();
  return text ? `/?${text}` : "/";
}
