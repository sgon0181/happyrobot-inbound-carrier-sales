import { RepActions } from "@/components/rep-actions";
import { EventList } from "@/components/ops-events";
import { DetailSheet, Facts, SheetSection } from "@/components/detail-sheet";
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
import { allowedActions, type Booking } from "@/lib/ops-service";
import { fmtCount, fmtShort, fmtTime, fmtUsd, label, na, nextAction } from "@/lib/format";

const TIME_NOTE =
  "The TMS timezone is unspecified. Source timestamps are assumed UTC and displayed in Central Time.";
const USD_NOTE = "Amounts are displayed as USD under the documented TMS-unit assumption.";
const COLUMNS: [string, string][] = [
  ["Load", "w-[7.5rem]"],
  ["Carrier", "w-[16%]"],
  ["Lane", ""],
  ["Pickup", "w-[8rem]"],
  ["Rate", "w-[6.5rem]"],
  ["Status", "w-[8.5rem]"],
  ["Action", "w-[10.5rem]"],
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
  now,
  liveBooking,
  empty = "No reservations in this view.",
}: {
  title: string;
  description: string;
  rows: Booking[];
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
                      <BookingSheet booking={b} liveBooking={liveBooking} now={now} />
                      <p className={sub}>{fmtShort(b.updatedAt)}</p>
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
                      <p className={sub}>Posted {fmtUsd(b.load?.postedRate ?? null)}</p>
                    </TableCell>
                    <TableCell className={cell}>
                      <StateBadge state={b.state} />
                      {b.state === "RESERVED" ? null : (
                        <p className="mt-1 text-xs text-muted-foreground">{nextAction(b.state)}</p>
                      )}
                    </TableCell>
                    <TableCell className={`${cell} pr-6`}>
                      <Actions booking={b} now={now} liveBooking={liveBooking} short />
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

function Actions({
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
      confirmDisabledReason={confirmReason(liveBooking, short)}
      confirmText={`Send ${b.loadId}, MC ${na(b.mc)}, at ${fmtUsd(b.rate)} once to the TMS? There is no supported cancellation.`}
    />
  );
}

function BookingSheet({ booking: b, liveBooking, now }: { booking: Booking; liveBooking: boolean | null; now: number }) {
  const load = b.load;
  const gap = b.rate !== null && load?.postedRate != null ? b.rate - load.postedRate : null;
  const versus =
    gap === null ? "Not recorded" : gap === 0 ? "At posted" : `${fmtUsd(Math.abs(gap))} ${gap > 0 ? "above" : "below"} posted`;
  return (
    <DetailSheet
      trigger={b.loadId}
      title={
        <span className="flex items-center gap-3">
          <span className="font-mono">{b.loadId}</span> <StateBadge state={b.state} />
        </span>
      }
      description={nextAction(b.state)}
    >
      <SheetSection title="Carrier">
        <Facts items={[["Carrier", na(b.carrierName)], ["MC", na(b.mc)], ["Call", <span key="c" className="font-mono text-xs">{na(b.callId)}</span>]]} />
      </SheetSection>
      <SheetSection title="Load">
        <Facts
          items={[
            ["Lane", `${na(load?.origin)} to ${na(load?.destination)}`],
            ["Equipment", label(load?.equipment)],
            ["Pickup", fmtTime(load?.pickup ?? null)],
            ["Delivery", fmtTime(load?.delivery ?? null)],
            ["Weight", `${fmtCount(load?.weight ?? null)} lbs`],
            ["Pieces", fmtCount(load?.pieces ?? null)],
            ["Miles", fmtCount(load?.miles ?? null)],
            ["Commodity", na(load?.commodity)],
            ["Dimensions", na(load?.dimensions)],
            ["Notes", na(load?.notes)],
          ]}
        />
        <p className="text-xs text-muted-foreground">{TIME_NOTE}</p>
      </SheetSection>
      <SheetSection title="Carrier payment">
        <Facts
          items={[
            ["Agreed", <strong key="a">{fmtUsd(b.rate)}</strong>],
            ["Posted", fmtUsd(load?.postedRate ?? null)],
            ["Versus posted", versus],
          ]}
        />
        <p className="text-xs text-muted-foreground">{USD_NOTE} Carrier payment, not brokerage revenue.</p>
      </SheetSection>
      <SheetSection title="TMS">
        <Facts
          items={[
            ["TMS status", label(b.tmsStatus)],
            ["Reference", na(b.reference)],
            ["Reason", label(b.reason)],
            ["Rep", na(b.rep)],
            ...(b.sendStep
              ? ([["Transport", <span key="t" className="font-mono text-xs break-all">{`${b.sendStep} ${b.sendError ?? ""}, ${fmtCount(b.sendBytes)} bytes, sha256 ${b.sendSha256}`}</span>]] as [string, React.ReactNode][])
              : []),
          ]}
        />
      </SheetSection>
      <SheetSection title="Next action">
        <Actions booking={b} now={now} liveBooking={liveBooking} />
      </SheetSection>
      <SheetSection title="Activity">
        <EventList events={b.events} />
      </SheetSection>
    </DetailSheet>
  );
}
