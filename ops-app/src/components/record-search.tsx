import { fmtTime, label } from "@/lib/format";
import type { Booking, Call } from "@/lib/snapshot";
import { viewHref, type View } from "@/lib/views";
import Link from "next/link";

export type Filters = { query: string; status: string; run: string; load: string; bucket: string; from: string; to: string };
export const missingClose = (c: Call) => c.outcome === "ended_without_close" || c.outcome === "end_not_recorded";
function matches(query: string, fields: (string | null | undefined)[]) {
  const needle = query.trim().toLowerCase();
  return !needle || fields.some((s) => s?.toLowerCase().includes(needle));
}
function inDates(at: string | null | undefined, f: Filters) {
  if (!f.from && !f.to) return true;
  if (!at) return false;
  const date = fmtTime(at).slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(date) && (!f.from || date >= f.from) && (!f.to || date <= f.to);
}
export function filterCalls(rows: Call[], f: Filters) {
  return rows.filter(c => matches(f.query, [c.mc, c.carrierName, c.bookingLoadId, c.search, ...(c.offeredIds ?? []), ...(c.offeredLanes ?? [])]) && inDates(c.sessionAt, f)
    && (!f.status || (f.status === "missing_close" ? missingClose(c) : c.outcome === f.status)));
}
export function filterBookings(rows: Booking[], f: Filters, byRun: Map<string, Call>) {
  return rows.filter(b => matches(f.query, [b.mc, b.carrierName, b.loadId, b.load?.origin, b.load?.destination, b.callId ? byRun.get(b.callId)?.search : null]) && inDates((b.callId && byRun.get(b.callId)?.sessionAt) || b.updatedAt, f) && (!f.status || b.state === f.status));
}
export function RecordSearch({ view, filters, statuses }: { view: View; filters: Filters; statuses: (string | null)[] }) {
  const codes = [...new Set(statuses.filter((s): s is string => Boolean(s)))].sort();
  const control = "rounded-md border bg-background px-3 py-2 text-sm";
  return <form key={[filters.query, filters.from, filters.to, filters.status, filters.bucket].join("|")} action="/" method="get" className="flex flex-wrap items-end gap-3">
    <input type="hidden" name="view" value={view} />
    {filters.bucket && <input type="hidden" name="bucket" value={filters.bucket} />}
    <label className="grid gap-1 text-xs font-medium">Find a record
      <input name="q" defaultValue={filters.query} placeholder="MC, carrier, load or lane" className={control} />
    </label>
    <label className="grid gap-1 text-xs font-medium">{view === "calls" ? "Call outcome" : "Booking status"}
      <select name="status" defaultValue={filters.status} className={control}>
        <option value="">All {view === "calls" ? "outcomes" : "statuses"}</option>
        {codes.map(s => <option value={s} key={s}>{s === "missing_close" ? "Closing record missing" : label(s)}</option>)}
      </select>
    </label>
    <label className="grid gap-1 text-xs font-medium">From (CT)<input name="from" type="date" defaultValue={filters.from} className={control} /></label>
    <label className="grid gap-1 text-xs font-medium">Through (CT)<input name="to" type="date" defaultValue={filters.to} className={control} /></label>
    <button type="submit" className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background">Search</button>
    {(filters.status || filters.query || filters.from || filters.to) && <Link href={viewHref(view)} className="py-2 text-sm underline">Clear</Link>}
  </form>;
}
