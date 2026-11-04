import Link from "next/link";

import { StatusPill } from "@/components/state-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Booking, Call } from "@/lib/snapshot";
import { fmtUsd, label, na } from "@/lib/format";
import { viewHref, type Scope } from "@/lib/views";

const STALE_SEND_MS = 60_000;

function age(at: string | null, now: number): string {
  const then = at ? Date.parse(at) : Number.NaN;
  if (Number.isNaN(then) || !now) return "time not recorded";
  const minutes = Math.max(0, Math.round((now - then) / 60_000));
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.round(minutes / 60);
  return hours < 48 ? `${hours} h` : `${Math.round(hours / 24)} d`;
}

type Item = { key: string; code: string; title: string; detail: string; href: string };

// What a rep should do next, most urgent first. Only facts from the snapshot, no guesses.
export function attention(bookings: Booking[], calls: Call[], now: number, scope: Scope): Item[] {
  const items: Item[] = [];
  for (const b of bookings) {
    if (b.state === "UNKNOWN")
      items.push({ key: b.loadId, code: "UNKNOWN", title: `${b.loadId}: send outcome unknown`, detail: "Reconcile with the TMS. Never resend.", href: viewHref("bookings", scope) });
    const since = b.updatedAt ? Date.parse(b.updatedAt) : Number.NaN;
    if (b.state === "SUBMITTING" && (Number.isNaN(since) || now - since >= STALE_SEND_MS))
      items.push({ key: b.loadId, code: "SUBMITTING", title: `${b.loadId}: send has not finished`, detail: "Reconcile after a minute.", href: viewHref("bookings", scope) });
  }
  for (const b of bookings.filter((r) => r.state === "RESERVED"))
    items.push({
      key: b.loadId,
      code: "RESERVED",
      title: `${b.loadId}: ${na(b.carrierName)} at ${fmtUsd(b.rate)}`,
      detail: `${na(b.load?.origin)} to ${na(b.load?.destination)}. Waiting ${age(b.updatedAt, now)} for a rep.`,
      href: viewHref("reservations", scope),
    });
  const unrecorded = calls.filter((c) => c.outcome === "ended_without_close" || c.outcome === "end_not_recorded").length;
  if (unrecorded)
    items.push({ key: "notes", code: "ended_without_close", title: `${unrecorded} call${unrecorded === 1 ? "" : "s"} without closing notes`, detail: "Review the call timeline before relying on the outcome.", href: viewHref("calls", scope) });
  return items;
}

export function Attention({ items, title = "Needs your review", description = "Submission problems first. Open a record to review the evidence and next action." }: { items: Item[]; title?: string; description?: string }) {
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        {!items.length ? (
          <p className="px-6 py-8 text-center text-sm text-muted-foreground">Nothing needs a rep right now.</p>
        ) : (
          <ul className="divide-y">
            {items.map((item) => (
              <li key={`${item.code}-${item.key}`}>
                <Link href={item.href} className="flex flex-col items-start gap-2 px-6 py-3 hover:bg-muted/40 sm:flex-row sm:gap-4">
                  <StatusPill code={item.code} className="mt-0.5 sm:w-44 sm:shrink-0 justify-start" />
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">{item.title}</span>
                    <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">{item.detail}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export function Outcomes({ calls }: { calls: Call[] }) {
  const counts = new Map<string, number>();
  for (const c of calls) counts.set(c.outcome ?? "in_progress", (counts.get(c.outcome ?? "in_progress") ?? 0) + 1);
  const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>Recorded call outcomes</CardTitle>
        <CardDescription>One outcome per call in this view, across all recorded history.</CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        {!rows.length ? (
          <p className="px-6 py-8 text-center text-sm text-muted-foreground">No calls yet.</p>
        ) : (
          <ul className="divide-y">
            {rows.map(([code, n]) => (
              <li key={code} className="flex items-center justify-between gap-3 px-6 py-2.5">
                <StatusPill code={code} />
                <span className="text-sm font-medium tabular-nums" title={label(code)}>{n}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
