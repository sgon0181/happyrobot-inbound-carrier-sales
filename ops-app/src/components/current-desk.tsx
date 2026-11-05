import Link from "next/link";
import { Attention, attention } from "@/components/overview";
import { fmtShort } from "@/lib/format";
import type { Booking } from "@/lib/snapshot";
import { recordHref } from "@/lib/views";

const panel = "rounded-xl border bg-card p-5";

export function reservationCounts(bookings: Booking[]) {
  return Object.fromEntries(["RESERVED", "ACK_PENDING", "CONFIRMED", "RELEASED"].map(state =>
    [state, bookings.filter(b => b.state === state).length]));
}

export function ReservationSummary({ bookings, now }: { bookings: Booking[]; now: number }) {
  const counts = reservationCounts(bookings);
  const oldest = bookings.filter(b => b.state === "RESERVED" && b.updatedAt && Number.isFinite(Date.parse(b.updatedAt)))
    .sort((a, b) => a.updatedAt!.localeCompare(b.updatedAt!))[0];
  const alerts = attention(bookings, [], now).filter(i => i.code === "UNKNOWN" || i.code === "SUBMITTING");
  const cards = [
    { state: "RESERVED", title: "Awaiting senior rep", href: "/?view=reservations&bucket=awaiting", description: "Review the agreement and originating call." },
    { state: "ACK_PENDING", title: "TMS acknowledged", href: "/?view=bookings&status=ACK_PENDING", description: "PENDING receipt received. Final booking unconfirmed." },
    { state: "CONFIRMED", title: "TMS confirmed", href: "/?view=bookings&status=CONFIRMED", description: "Bookings with an authoritative BOOKED receipt." },
    { state: "RELEASED", title: "Released reservations", href: "/?view=bookings&status=RELEASED", description: "Released before a booking submission." },
  ];
  return <section className="space-y-3">
    <div><h2 className="text-xl font-semibold">Reservation status</h2>
      <p className="mt-1 text-sm text-muted-foreground">Latest state of each load reservation. The funnel above counts agreements by call, including earlier agreements on reused loads.</p></div>
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{cards.map(card =>
      <Link key={card.state} className={panel + " hover:bg-muted/30"} href={card.href}>
        <h3 className="text-sm font-semibold">{card.title}</h3><p className="my-2 text-3xl font-semibold">{counts[card.state]}</p>
        <p className="text-sm text-muted-foreground">{card.description}</p>
      </Link>)}</div>
    {oldest && <Link className="block text-sm underline" href={recordHref("reservations", oldest.loadId, oldest.callId)}>
      Oldest awaiting review: {oldest.loadId} · {fmtShort(oldest.updatedAt)}</Link>}
    {alerts.length > 0 && <Attention title="Submission exceptions" description="Review ambiguous receipts and stalled submissions before another action." items={alerts} />}
  </section>;
}
