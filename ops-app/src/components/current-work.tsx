import Link from "next/link";
import type { Booking } from "@/lib/snapshot";
import { fmtCount } from "@/lib/format";
import { viewHref, type Scope } from "@/lib/views";

// Current load ownership and submission states, separate from historical call totals.
export function CurrentWork({ bookings, scope }: { bookings: Booking[]; scope: Scope }) {
  const count = (state: string) => bookings.filter((b) => b.state === state).length;
  const tiles: [string, number, string, "reservations" | "bookings"][] = [
    ["Awaiting rep review", count("RESERVED"), "Agreed with the carrier; no booking sent", "reservations"],
    ["Submission outcome unknown", count("UNKNOWN"), "Investigate before taking any further action", "bookings"],
    ["Awaiting TMS confirmation", count("ACK_PENDING"), "Request acknowledged as PENDING, not final", "bookings"],
    ["TMS-confirmed bookings", count("CONFIRMED"), "Final BOOKED response received", "bookings"],
  ];
  return (
    <section aria-label="Current reservations and bookings" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {tiles.map(([name, value, hint, view]) => (
        <Link key={name} href={viewHref(view, scope)} className="rounded-xl border bg-card p-4 transition-colors hover:bg-muted/40">
          <h2 className="text-sm font-medium">{name}</h2>
          <p className="mt-2 text-3xl font-semibold tabular-nums">{fmtCount(value)}</p>
          <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{hint}</p>
        </Link>
      ))}
    </section>
  );
}
