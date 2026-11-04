import type { Call } from "@/lib/snapshot";
import { CallLog } from "@/components/call-log";
import { TurnedAway, lanesFrom } from "@/components/turned-away";
import Link from "next/link";
import { demoVoiceRunIds } from "@/lib/demo-voice-runs";
import { viewHref } from "@/lib/views";

export function DemandReport({ calls, bucket }: { calls: Call[]; bucket: string }) {
  const unresolved = calls.filter(c => c.codePassed && !c.foundMatch && !c.bookingLoadId);
  const ended = (c: Call) => Boolean(c.endedAt || c.closedAt || demoVoiceRunIds.has(c.id));
  const verified = unresolved.filter(ended);
  const unknown = unresolved.filter(c => !ended(c));
  const groups = [
    { key: "empty", label: "Search returned no freight", rows: verified.filter(c => c.noMatchSeen) },
    { key: "none", label: "No search recorded", rows: verified.filter(c => !c.searchAttempted) },
    { key: "other", label: "Search without a usable result", rows: verified.filter(c => c.searchAttempted && !c.noMatchSeen) },
  ];
  const group = bucket === "unknown" ? {label:"End not confirmed",rows:unknown} : groups.find(g => g.key === bucket);
  const base = viewHref("demand");
  return <section className="space-y-4">
    <div><h2 className="text-xl font-semibold">Unfilled carrier requests</h2><p className="mt-1 text-sm text-muted-foreground">Verified callers who left without a matching load or reservation.</p></div>
    <div className="grid gap-3 sm:grid-cols-3">{groups.map(g =>
      <Link key={g.key} href={`${base}&bucket=${g.key}`} className="rounded-xl border bg-card p-4 hover:bg-muted/40">
        <p className="text-sm font-medium">{g.label}</p><strong className="mt-1 block text-2xl">{g.rows.length}</strong>
      </Link>)}</div>
    {group ? <CallLog title={group.label} calls={group.rows} /> : <TurnedAway lanes={lanesFrom(verified)} />}
    <Link href={base + "&bucket=unknown"} className="text-sm underline">End not confirmed ({unknown.length}). These calls are excluded from unfilled requests.</Link>
  </section>;
}
