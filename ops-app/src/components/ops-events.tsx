import type { EventRow } from "@/lib/event-history";
import { fmtCount, fmtTime, fmtUsd, label, na } from "@/lib/format";

// Business activity first; technical identifiers remain available without dominating the timeline.
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
          <details className="mt-2 text-muted-foreground">
            <summary className="cursor-pointer text-[0.6875rem]">Technical details</summary>
            <p className="mt-1 font-mono text-[0.6875rem] break-all">{[e.action, e.status, e.state].filter(Boolean).join(" / ")}</p>
            {e.callId ? <p className="mt-1 font-mono text-[0.6875rem] break-all">Call reference: {e.callId}</p> : null}
          </details>
        </li>
      ))}
    </ol>
  );
}
