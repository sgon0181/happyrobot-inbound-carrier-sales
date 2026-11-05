import Link from "next/link";
import { Facts, SheetSection } from "@/components/detail-sheet";
import { EventList } from "@/components/ops-events";
import { BookingActions } from "@/components/rep-queue";
import { StateBadge } from "@/components/state-badge";
import { fmtCount, fmtTime, fmtUsd, label, na, nextAction, submissionStatus } from "@/lib/format";
import type { Booking, Call } from "@/lib/snapshot";
import { viewHref } from "@/lib/views";

const box = "rounded-xl border bg-card p-5";
const labels = "text-xs font-medium text-muted-foreground";

export function ReservationReview({ booking: b, call: c, now, live, canManage }: {
  booking?: Booking; call?: Call; canManage: boolean; now: number; live: boolean | null;
}) {
  const load = b?.load;
  const loadId = b?.loadId ?? c?.bookingLoadId;
  if (!loadId) return <p role="status" className={box}>This reservation is unavailable in the selected activity.</p>;
  const opening = c?.openingRate ?? null;
  const agreed = c?.agreedRate ?? b?.rate ?? null;
  const state = b?.state ?? c?.bookingState ?? null;
  const gap = opening !== null && agreed !== null ? agreed - opening : null;
  const runUrl = c?.recordingUrl;
  const queue = b && state !== "RESERVED" && state !== "RELEASED" ? "bookings" : "reservations";
  return <section className="space-y-4">
    <Link href={viewHref(queue)} className="text-sm underline">Back to {queue === "reservations" ? "reservations" : "bookings"}</Link>
    <div className={box}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-2xl font-semibold"> {queue === "bookings" ? "Booking review" : "Reservation review"} · {loadId}</h2><StateBadge state={state} />
      </div>
      <p className="mt-2 font-medium">{na(b?.carrierName ?? c?.carrierName)} · MC {na(b?.mc ?? c?.mc)}</p>
      {runUrl && <a href={runUrl} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-sm font-medium text-teal-800 underline underline-offset-2">Open recording and transcript in HappyRobot</a>}
      {c && <a href="#timeline" className="ml-3 text-sm underline underline-offset-2">View call timeline</a>}
      <p className="mt-1 text-sm">{load ? `${na(load.origin)} to ${na(load.destination)} · ${label(load.equipment)}` : na(c?.search)}</p>
      <div className="my-4 grid grid-cols-2 gap-4 border-y py-3 sm:grid-cols-4">
        {[
          ["Opening offer", fmtUsd(opening)], [b?.agreementNeedsReview ? "Held amount" : "Agreed rate", fmtUsd(agreed)],
          ["Agent counteroffers", fmtCount(c?.counters ?? null)], ["Pricing rounds used", fmtCount(c?.rounds ?? null)],
        ].map(([name, value]) => <div key={name}><p className={labels}>{name}</p><p className="mt-1 text-lg font-semibold">{value}</p></div>)}
      </div>
      {gap !== null && !b?.agreementNeedsReview && <p className="mb-2 text-sm">{gap === 0 ? "Agreed at the opening offer." : `Agreed ${fmtUsd(Math.abs(gap))} ${gap < 0 ? "below" : "above"} the opening offer.`}</p>}
      <p className="text-sm">{b?.agreementNeedsReview ? "A load hold was created, but the originating call has no finished agreement. Check with the carrier before creating a fresh reservation." : b ? nextAction(state) : "Historical agreement. Current load ownership has changed."}</p>
      {b && !canManage && <p className="mt-2 text-sm text-muted-foreground">View only. A designated senior rep can act on this reservation.</p>}
      {b && canManage && <div className="mt-2"><BookingActions booking={b} liveBooking={live} now={now} /></div>}
    </div>
    {b && <div className={box}><SheetSection title="Booking and shipment">
      <Facts items={[["TMS status", submissionStatus(b.state, b.reason, b.tmsStatus)], ["Reference", na(b.reference)],
        ["Pickup", fmtTime(load?.pickup ?? null)], ["Delivery", fmtTime(load?.delivery ?? null)],
        ["Weight", load?.weight != null ? `${fmtCount(load.weight)} lbs` : "Not recorded"], ["Distance", load?.miles != null ? `${fmtCount(load.miles)} mi` : "Not recorded"],
        ["Equipment", label(load?.equipment)], ["Pieces", fmtCount(load?.pieces ?? null)], ["Dimensions", na(load?.dimensions)],
        ["Posted rate", fmtUsd(load?.postedRate ?? null)], ["Rep", na(b.rep)], ["Reason", label(b.reason)], ["Commodity", na(load?.commodity)], ["Shipment notes", na(load?.notes)]]} />
    </SheetSection></div>}
    <div className={box} id="timeline"><h3 className="mb-2 font-semibold">Originating call timeline</h3>
      {c ? <><p className="mb-4 text-sm text-muted-foreground">{fmtTime(c.startedAt)} · {c.codePassed ? "Email verified" : "Email verification not recorded"} · {c.summary || "No closing notes recorded."}</p>
        <EventList events={c.events} /></> : <p>Call activity has not been recorded for this reservation.</p>}
    </div>
    {b && <details className={box}><summary className="cursor-pointer font-medium">Reservation and submission history</summary><div className="mt-4"><EventList events={b.events} /></div></details>}
  </section>;
}
