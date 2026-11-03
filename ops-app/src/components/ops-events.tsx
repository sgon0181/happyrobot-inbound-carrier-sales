import type { EventRow } from "@/lib/event-history";
import { fmtCount, fmtTime, fmtUsd, label, na } from "@/lib/format";
export function EventList({ events }: { events: EventRow[] }) {
  if (!events.length) return <p>No activity recorded.</p>;
  return (
    <ol className="flex flex-col gap-2 text-xs break-words">
      {events.map((e, i) => (
        <li key={e.seq ?? i}>
          <strong>
            {fmtTime(e.at)}: {label(e.action)}
          </strong>{" "}
          {[e.status, e.state, e.reason]
            .filter(Boolean)
            .map((v) => label(v))
            .join("; ")}
          {e.rep ? `; rep ${e.rep}` : ""}
          {e.detail ? (
            <p className="text-muted-foreground">{e.detail}</p>
          ) : null}
          {e.load ? <div className="mt-1 text-muted-foreground">
            <p>Reservation terms: {na(e.load.origin)} to {na(e.load.destination)}; {label(e.load.equipment)}.</p>
            <p>Pickup: {fmtTime(e.load.pickup)}. Delivery: {fmtTime(e.load.delivery)}. Posted: {fmtUsd(e.load.postedRate)}.</p>
            <p>Weight: {fmtCount(e.load.weight)} lbs. Pieces: {fmtCount(e.load.pieces)}. Miles: {fmtCount(e.load.miles)}.</p>
            <p>Commodity: {na(e.load.commodity)}. Dimensions: {na(e.load.dimensions)}. Notes: {na(e.load.notes)}.</p>
          </div> : null}
          <span className="font-mono text-muted-foreground">
            {[e.action, e.status, e.state].filter(Boolean).join(" / ")}
          </span>
        </li>
      ))}
    </ol>
  );
}
