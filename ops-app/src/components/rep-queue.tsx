import { Fragment } from "react";
import { RepActions } from "@/components/rep-actions";
import { EventList } from "@/components/ops-events";
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
import { fmtCount, fmtTime, fmtUsd, label, na, nextAction } from "@/lib/format";

const cell = "py-3 text-left align-top whitespace-normal";
const TIME_NOTE =
  "The TMS timezone is unspecified. Source timestamps are assumed UTC and displayed in Central Time.";
export function RepQueue({
  title,
  description,
  rows,
  now,
  liveBooking,
}: {
  title: string;
  description: string;
  rows: Booking[];
  now: number;
  liveBooking: boolean | null;
}) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="min-w-0">
        <div className="max-h-[40rem] w-full min-w-0 overflow-auto">
          <Table className="w-full min-w-[900px]">
            <TableHeader className="sticky top-0 bg-card">
              <TableRow>
                {[
                  "Load and carrier",
                  "Lane and equipment",
                  "Pickup and delivery (CT)",
                  "Carrier payment",
                  "Status and next action",
                ].map((h) => (
                  <TableHead key={h}>{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {!rows.length ? (
                <TableRow>
                  <TableCell colSpan={5}>
                    No reservations in this view.
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((b) => (
                  <Fragment key={b.loadId}>
                    <TableRow className="hover:bg-muted/40">
                      <TableCell className={cell}>
                        <strong className="font-mono">{b.loadId}</strong>
                        <p>{na(b.carrierName)}</p>
                        <p>MC {na(b.mc)}</p>
                      </TableCell>
                      <TableCell className={cell}>
                        <p>{na(b.load?.origin)}</p>
                        <p>to {na(b.load?.destination)}</p>
                        <p>{label(b.load?.equipment)}</p>
                      </TableCell>
                      <TableCell className={cell} title={TIME_NOTE}>
                        <p>Pickup: {fmtTime(b.load?.pickup ?? null)}</p>
                        <p>Delivery: {fmtTime(b.load?.delivery ?? null)}</p>
                      </TableCell>
                      <TableCell
                        className={cell}
                        title="Amounts are displayed as USD under the documented TMS-unit assumption."
                      >
                        <p>
                          Agreed: <strong>{fmtUsd(b.rate)}</strong>
                        </p>
                        <p>Posted: {fmtUsd(b.load?.postedRate ?? null)}</p>
                      </TableCell>
                      <TableCell className={`${cell} min-w-60`}>
                        <StateBadge state={b.state} />
                        <p className="my-2 text-xs">{nextAction(b.state)}</p>
                        <RepActions
                          loadId={b.loadId}
                          version={b.version}
                          actions={allowedActions(b, now)}
                          confirmDisabledReason={liveBooking === true ? null : liveBooking === false ? "Booking sends are off. Confirm is disabled." : "Send mode unavailable. Confirm is disabled."}
                    confirmText={`Send ${b.loadId}, MC ${na(b.mc)}, at ${fmtUsd(b.rate)} once to the TMS? There is no supported cancellation.`}
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={5} className="whitespace-normal">
                        <details>
                          <summary className="cursor-pointer py-1 text-sm underline">
                            Deal details and activity for {b.loadId}
                          </summary>
                          <div className="grid gap-4 p-3 md:grid-cols-2">
                            <div className="text-sm">
                              <p>
                                Weight: {fmtCount(b.load?.weight ?? null)} lbs.
                                Miles: {fmtCount(b.load?.miles ?? null)}.
                              </p>
                              <p>
                                Commodity: {na(b.load?.commodity)}. Dimensions:{" "}
                                {na(b.load?.dimensions)}.
                              </p>
                              <p>Notes: {na(b.load?.notes)}</p>
                              <p>
                                TMS: {label(b.tmsStatus)}. Reference:{" "}
                                {na(b.reference)}.
                              </p>
                              <p>
                                Rep: {na(b.rep)}. Reason: {label(b.reason)}.
                              </p>
                              <p>
                                Last recorded activity: {fmtTime(b.updatedAt)}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {TIME_NOTE}
                              </p>
                              {b.sendStep ? (
                                <p className="break-all font-mono text-xs">
                                  Transport: {b.sendStep} {b.sendError},{" "}
                                  {fmtCount(b.sendBytes)} bytes, sha256{" "}
                                  {b.sendSha256}
                                </p>
                              ) : null}
                            </div>
                            <EventList events={b.events} />
                          </div>
                        </details>
                      </TableCell>
                    </TableRow>
                  </Fragment>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
