import type { EventRow } from "@/lib/event-history";
import { fmtTime, label } from "@/lib/format";
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
          <span className="font-mono text-muted-foreground">
            {[e.action, e.status, e.state].filter(Boolean).join(" / ")}
          </span>
        </li>
      ))}
    </ol>
  );
}
