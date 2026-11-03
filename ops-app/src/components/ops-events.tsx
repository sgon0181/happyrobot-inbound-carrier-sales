import type { EventRow } from "@/lib/event-history";
import { fmtCount, fmtTime, fmtUsd, label, na } from "@/lib/format";

// The stored activity as a timeline, oldest first, with the raw codes kept for audit.
export function EventList({ events }: { events: EventRow[] }) {
  if (!events.length) return <p className="text-sm text-muted-foreground">No activity recorded.</p>;
  return (
    <ol className="relative flex flex-col gap-4 border-l pl-5 text-xs break-words">
      {events.map((e, i) => (
        <li key={e.seq ?? i} className="relative">
          <span aria-hidden className="absolute top-1 -left-[1.5625rem] size-2 rounded-full bg-foreground/70 ring-4 ring-background" />
          <p className="text-sm">
            <strong className="font-medium">{label(e.action)}</strong>{" "}
            <span className="text-muted-foreground">
              {[e.status, e.state, e.reason].filter(Boolean).map((v) => label(v)).join("; ")}
              {e.rep ? `; rep ${e.rep}` : ""}
            </span>
          </p>
          <p className="text-muted-foreground">{fmtTime(e.at)}</p>
          {e.detail ? <p className="mt-1">{e.detail}</p> : null}
          {e.load ? (
            <div className="mt-1 rounded-md bg-muted/60 p-2 text-muted-foreground">
              <p>Reservation terms: {na(e.load.origin)} to {na(e.load.destination)}; {label(e.load.equipment)}.</p>
              <p>Pickup: {fmtTime(e.load.pickup)}. Delivery: {fmtTime(e.load.delivery)}. Posted: {fmtUsd(e.load.postedRate)}.</p>
              <p>Weight: {fmtCount(e.load.weight)} lbs. Pieces: {fmtCount(e.load.pieces)}. Miles: {fmtCount(e.load.miles)}.</p>
              <p>Commodity: {na(e.load.commodity)}. Dimensions: {na(e.load.dimensions)}. Notes: {na(e.load.notes)}.</p>
            </div>
          ) : null}
          <span className="font-mono text-[0.6875rem] text-muted-foreground/80">
            {[e.action, e.status, e.state].filter(Boolean).join(" / ")}
          </span>
        </li>
      ))}
    </ol>
  );
}
