import Link from "next/link";
import { Attention, attention } from "@/components/overview";
import { fmtShort } from "@/lib/format";
import type { Booking, Call } from "@/lib/snapshot";
import { recordHref } from "@/lib/views";

const panel = "rounded-xl border bg-card p-5";
const day = 86_400_000;

export function deskWindow(calls: Call[], now: number) {
  return calls.filter(c => {
    const at = Date.parse(c.sessionAt ?? "");
    return c.cohort === "real" && at > now - 7 * day && at <= now;
  });
}

export function CurrentDesk({ bookings, calls, now }: { bookings: Booking[]; calls: Call[]; now: number }) {
  const real = bookings.filter(b => b.cohort === "real");
  const waiting = real.filter(b => b.state === "RESERVED");
  const pending = real.filter(b => b.state === "ACK_PENDING");
  const oldest = [...waiting].filter(b => b.updatedAt && Number.isFinite(Date.parse(b.updatedAt)))
    .sort((a, b) => a.updatedAt!.localeCompare(b.updatedAt!))[0];
  const recent = deskWindow(calls, now);
  const verified = recent.filter(c => c.codePassed);
  const reserved = verified.filter(c => c.bookingLoadId !== null);
  const alerts = attention(real, [], now).filter(i => i.code === "UNKNOWN" || i.code === "SUBMITTING");
  return <section className="space-y-4">
    <div><p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Current desk</p>
      <h2 className="mt-1 text-2xl font-semibold">Handoffs and exceptions</h2>
      <p className="mt-1 text-sm text-muted-foreground">Only calls tagged real by the service appear here. The Reservations queue also includes historical trials. Snapshot {fmtShort(new Date(now).toISOString())}.</p></div>
    <div className="grid gap-3 sm:grid-cols-3">
      <div className={panel}><h3 className="text-sm font-semibold">Awaiting senior rep</h3><p className="my-2 text-3xl font-semibold">{waiting.length}</p>
        {oldest ? <Link className="text-sm underline" href={recordHref("reservations",oldest.loadId,oldest.callId)}>Oldest reservation · {oldest.loadId} · {fmtShort(oldest.updatedAt)}</Link> : <p className="text-sm text-muted-foreground">{waiting.length ? "Reservation times unavailable." : "No reservations waiting."}</p>}</div>
      <Link className={panel} href="/?view=bookings&status=ACK_PENDING&bucket=desk"><h3 className="text-sm font-semibold">Acknowledged, pending</h3><p className="my-2 text-3xl font-semibold">{pending.length}</p><p className="text-sm text-muted-foreground">Inspect receipts for requests the TMS acknowledged.</p></Link>
      <div className={panel}><h3 className="text-sm font-semibold">Verified calls with a reservation</h3><p className="my-2 text-3xl font-semibold">{verified.length ? Math.round(100*reserved.length/verified.length)+"%" : "No rate yet"}</p><p className="text-sm text-muted-foreground">{reserved.length} of {verified.length} verified · Last 7 days · {recent.length} calls</p></div>
    </div>
    {calls.some(c => c.cohort === "real" && c.outcome === "shipment_review_required") &&
      <Link className={panel + " block"} href="/?view=calls&bucket=desk&status=shipment_review_required">
        <strong>Shipment terms need review</strong>
        <p className="mt-1 text-sm text-muted-foreground">Open the call timeline for the affected load IDs. Check their operating terms before offering the freight.</p>
      </Link>}
    <Attention title="Submission exceptions" description="Review ambiguous receipts and stalled submissions before another rep takes action." items={alerts} />
  </section>;
}
