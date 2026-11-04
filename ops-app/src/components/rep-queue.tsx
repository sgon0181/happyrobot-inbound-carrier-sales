import Link from "next/link";
import { recordHref } from "@/lib/views";
import { RepActions } from "@/components/rep-actions";
import { StateBadge } from "@/components/state-badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { allowedActions, type Booking, type Call } from "@/lib/ops-service";
import { fmtCount, fmtShort, fmtUsd, label, na, nextAction, submissionStatus } from "@/lib/format";

const TIME_NOTE =
  "The TMS timezone is unspecified. Source timestamps are assumed UTC and displayed in Central Time.";
const USD_NOTE = "Amounts are displayed as USD under the documented TMS-unit assumption.";
const COLUMNS: [string, string][] = [
  ["Load", "w-[7.5rem]"],
  ["Carrier", "w-[16%]"],
  ["Lane", ""],
  ["Pickup", "w-[8rem]"],
  ["Agreed rate", "w-[6.5rem]"],
  ["Status", "w-[10.5rem]"],
  ["Action", "w-[8rem]"],
];
const cell = "py-3 align-top whitespace-normal";
const sub = "truncate text-xs text-muted-foreground";

function confirmReason(liveBooking: boolean | null, short: boolean): string | null {
  if (liveBooking === true) return null;
  if (short) return liveBooking === false ? "Sends off" : "Send mode unknown";
  return liveBooking === false
    ? "Booking sends are off. Confirm is disabled."
    : "Send mode unavailable. Confirm is disabled.";
}

export function RepQueue({
  title,
  description,
  rows,
  callById = new Map(),
  empty = "No reservations in this view.",
}: {
  title: string;
  description: string;
  rows: Booking[];
  callById?: Map<string, Call>;
  now: number;
  liveBooking: boolean | null;
  empty?: string;
}) {
  return (
    <Card className="min-w-0 gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>
          {title} <span className="ml-1 font-normal text-muted-foreground tabular-nums">{rows.length}</span>
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="min-w-0 px-0">
        <div className="max-h-[42rem] overflow-y-auto">
          <Table className="table-fixed">
            <TableHeader className="sticky top-0 z-[1] bg-muted/70 backdrop-blur">
              <TableRow>
                {COLUMNS.map(([name, width]) => (
                  <TableHead key={name} className={`${width} px-3 text-xs text-muted-foreground first:pl-6`}>
                    {name}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {!rows.length ? (
                <TableRow>
                  <TableCell colSpan={COLUMNS.length} className="px-6 py-8 text-center text-muted-foreground">
                    {empty}
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((b) => (
                  <TableRow key={b.loadId} className="hover:bg-muted/40">
                    <TableCell className={`${cell} pl-6`}>
                      <Link href={recordHref(b.state === "RESERVED" ? "reservations" : "bookings", b.loadId, b.callId)} className="font-mono font-semibold underline underline-offset-2">{b.loadId}</Link>
                      <p className={sub}>Call {fmtShort(b.callId ? callById.get(b.callId)?.sessionAt ?? null : null)}</p>
                    </TableCell>
                    <TableCell className={cell}>
                      <p className="line-clamp-2 font-medium">{na(b.carrierName)}</p>
                      <p className={sub}>MC {na(b.mc)}</p>
                    </TableCell>
                    <TableCell className={cell}>
                      {b.load ? (
                        <>
                          <p>{na(b.load.origin)}</p>
                          <p>
                            <span className="text-muted-foreground">to</span> {na(b.load.destination)}
                          </p>
                          <p className={sub}>
                            {label(b.load.equipment)}
                            {b.load.miles ? `, ${fmtCount(b.load.miles)} mi` : ""}
                          </p>
                        </>
                      ) : (
                        <p className="text-muted-foreground">Not recorded</p>
                      )}
                    </TableCell>
                    <TableCell className={cell} title={TIME_NOTE}>
                      <p className="tabular-nums">{fmtShort(b.load?.pickup ?? null)}</p>
                    </TableCell>
                    <TableCell className={cell} title={USD_NOTE}>
                      <p className="font-semibold tabular-nums">{fmtUsd(b.rate)}</p>
                      <p className="text-xs text-muted-foreground">Opened {fmtUsd(b.callId ? callById.get(b.callId)?.openingRate ?? null : null)}</p>
                    </TableCell>
                    <TableCell className={cell}>
                      <StateBadge state={b.state} />
                      {b.state === "RESERVED" ? null : (
                        <p className="mt-1 text-xs text-muted-foreground">{b.state === "FAILED" ? submissionStatus(b.state, b.reason, b.tmsStatus) : nextAction(b.state)}</p>
                      )}
                    </TableCell>
                    <TableCell className={`${cell} pr-6`}>
                      <Link className="inline-block rounded-md border px-2 py-1.5 text-xs font-semibold hover:bg-muted" href={recordHref(b.state === "RESERVED" ? "reservations" : "bookings", b.loadId, b.callId)}>
                        {b.state === "RESERVED" ? "Review reservation" : "Review booking"}
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

export function BookingActions({
  booking: b,
  now,
  liveBooking,
  short = false,
}: {
  booking: Booking;
  now: number;
  liveBooking: boolean | null;
  short?: boolean;
}) {
  const actions = allowedActions(b, now);
  if (!actions.length) return <p className="text-xs text-muted-foreground">No action</p>;
  return (
    <RepActions
      loadId={b.loadId}
      version={b.version}
      actions={actions}
      confirmDisabledReason={b.cohort === "synthetic" && liveBooking === true ? "Demo reservation. Booking sends are off for this record." : confirmReason(liveBooking, short)}
      confirmText={`Send ${b.loadId}, MC ${na(b.mc)}, at ${fmtUsd(b.rate)} once to the TMS? There is no supported cancellation.`}
    />
  );
}
