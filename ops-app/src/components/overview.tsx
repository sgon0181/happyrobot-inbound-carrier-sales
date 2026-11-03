import Link from "next/link";

import { StatusPill } from "@/components/state-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Booking, Call, Kpis } from "@/lib/snapshot";
import { fmtCount, fmtUsd, label, na } from "@/lib/format";
import { viewHref, type Scope } from "@/lib/views";

const STALE_SEND_MS = 60_000;
const APPROVED = new Set(["SUBMITTING", "ACK_PENDING", "CONFIRMED", "UNKNOWN"]);
const ACKNOWLEDGED = new Set(["ACK_PENDING", "CONFIRMED"]);

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

export function Attention({ items }: { items: Item[] }) {
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>Needs attention <span className="ml-1 font-normal text-muted-foreground tabular-nums">{items.length}</span></CardTitle>
        <CardDescription>Reservations waiting for a rep, sends to reconcile and calls missing notes.</CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        {!items.length ? (
          <p className="px-6 py-8 text-center text-sm text-muted-foreground">Nothing needs a rep right now.</p>
        ) : (
          <ul className="divide-y">
            {items.map((item) => (
              <li key={`${item.code}-${item.key}`}>
                <Link href={item.href} className="flex items-start gap-3 px-6 py-3 hover:bg-muted/40">
                  <StatusPill code={item.code} className="mt-0.5 w-40 shrink-0 justify-start" />
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{item.title}</span>
                    <span className="block truncate text-xs text-muted-foreground">{item.detail}</span>
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

// From a call to a submitted booking, for the calls shown. Each step is a subset of the one before.
export function Funnel({ calls, bookings }: { calls: Call[]; bookings: Booking[] }) {
  const steps: [string, number, string][] = [
    ["Calls", calls.length, "Recorded call rows"],
    ["Code passed", calls.filter((c) => c.codePassed).length, "Passed the emailed code"],
    ["Rate agreed", calls.filter((c) => c.bookingLoadId).length, "Saved a reservation"],
    ["Rep approved", bookings.filter((b) => APPROVED.has(b.state ?? "")).length, "Sent once to the TMS"],
    ["TMS acknowledged", bookings.filter((b) => ACKNOWLEDGED.has(b.state ?? "")).length, "PENDING or BOOKED reply"],
  ];
  const top = Math.max(1, steps[0][1]);
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>Call to booking</CardTitle>
        <CardDescription>Where calls stop. PENDING is an acknowledgement, not a final booking.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 py-5">
        {steps.map(([name, value, hint]) => (
          <div key={name} className="grid grid-cols-[8.5rem_1fr_3.5rem] items-center gap-3 text-sm">
            <span className="truncate" title={hint}>{name}</span>
            <span className="h-2 overflow-hidden rounded-full bg-muted">
              <span className="block h-full rounded-full bg-foreground/80" style={{ width: `${Math.round((value / top) * 100)}%` }} />
            </span>
            <span className="text-right font-medium tabular-nums">{fmtCount(value)}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function KpiStrip({ kpis }: { kpis: Kpis }) {
  const tiles: [string, string, string][] = [
    ["Northstar", kpis.northstar === null ? "n/a" : `${Math.round(kpis.northstar * 100)}%`, "Recorded reservations per call that ever passed its code."],
    ["Calls", fmtCount(kpis.calls), "Real call rows saved by a service request or end report."],
    ["Code passed", fmtCount(kpis.codePassed), "Calls that passed a code at least once; not proof of carrier identity."],
    ["Reservations", fmtCount(kpis.handoffs), "Calls with a saved reservation, not proof of a spoken handoff."],
    ["Rep approved", fmtCount(kpis.repConfirmed), "Reservations approved for submission, not final TMS bookings."],
    ["TMS pending", fmtCount(kpis.tmsAcknowledged), `Reference with PENDING. TMS confirmed (BOOKED): ${fmtCount(kpis.tmsConfirmed)}.`],
    ["Unknown", fmtCount(kpis.unknown), "Sends that may have landed. Reconcile; never resend."],
    ["Tool-to-offer", kpis.medianSecondsToFirstOffer === null ? "n/a" : `${Math.round(kpis.medianSecondsToFirstOffer)} s`, "Median first service request to first matched search; excludes greeting and spoken delivery."],
  ];
  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold">Real calls</h2>
        <p className="text-xs text-muted-foreground">
          Test calls excluded: {fmtCount(kpis.syntheticCalls)}. End reports: {fmtCount(kpis.endsReported)}. Closing notes: {fmtCount(kpis.closedWithSummary)}.
        </p>
      </div>
      <div className="grid grid-cols-2 divide-x divide-y overflow-hidden rounded-xl border bg-card sm:grid-cols-4 xl:grid-cols-8 xl:divide-y-0">
        {tiles.map(([name, value, hint]) => (
          <div key={name} className="flex flex-col gap-1 p-4" title={hint}>
            <span className="truncate text-xs text-muted-foreground">{name}</span>
            <span className="text-2xl font-semibold tabular-nums">{value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Outcomes({ calls }: { calls: Call[] }) {
  const counts = new Map<string, number>();
  for (const c of calls) counts.set(c.outcome ?? "in_progress", (counts.get(c.outcome ?? "in_progress") ?? 0) + 1);
  const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>Outcomes</CardTitle>
        <CardDescription>How the calls shown ended, from the service&apos;s records.</CardDescription>
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
