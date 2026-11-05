import Link from "next/link";
import { recordHref } from "@/lib/views";
import { EventList } from "@/components/ops-events";
import { DetailSheet, Facts, SheetSection } from "@/components/detail-sheet";
import { StateBadge, StatusPill } from "@/components/state-badge";
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
import type { Call } from "@/lib/snapshot";
import { fmtCount, fmtShort, fmtTime, fmtUsd, label, na } from "@/lib/format";

const COLUMNS: [string, string][] = [
  ["Call", "w-[8.5rem]"],
  ["Carrier", "w-[19%]"],
  ["Lane asked", "w-[16%]"],
  ["Outcome", "w-[11.5rem]"],
  ["Agreement", "w-[7rem]"],
  ["Closing notes", ""],
];
const cell = "py-3 align-top whitespace-normal";
const sub = "truncate text-xs text-muted-foreground";

export function CallLog({ title, calls }: { title: string; calls: Call[] }) {
  return (
    <Card className="min-w-0 gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>
          {title} <span className="ml-1 font-normal text-muted-foreground tabular-nums">{calls.length}</span>
        </CardTitle>
        <CardDescription>
          Stored service activity, not a verbatim conversation or proof of a completed transfer. Open a call for its timeline.
        </CardDescription>
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
              {!calls.length ? (
                <TableRow>
                  <TableCell colSpan={COLUMNS.length} className="px-6 py-8 text-center text-muted-foreground">
                    No calls recorded in this view.
                  </TableCell>
                </TableRow>
              ) : (
                calls.map((c) => (
                  <TableRow key={c.id} className="hover:bg-muted/40">
                    <TableCell className={`${cell} pl-6`}>
                      <CallSheet call={c} />
                    </TableCell>
                    <TableCell className={cell}>
                      <p className="line-clamp-2 font-medium">{na(c.carrierName)}</p>
                      <p className={sub}>
                        MC {na(c.mc)} · {c.codePassed ? "email code verified" : "email not verified"}
                      </p>
                    </TableCell>
                    <TableCell className={cell}>
                      <p className="line-clamp-2">{lane(c.search)}</p>
                    </TableCell>
                    <TableCell className={cell}>
                      <StatusPill code={c.outcome} />
                      <p className="mt-1 text-xs text-muted-foreground">
                        {fmtCount(c.counters ?? null)} agent counteroffer{c.counters === 1 ? "" : "s"}
                      </p>
                    </TableCell>
                    <TableCell className={cell}>
                      {c.bookingLoadId ? (
                        <>
                          <Link className="font-mono text-sm underline" href={recordHref("reservations", c.bookingLoadId, c.id)}>{c.bookingLoadId}</Link>
                          <p className={sub}>{fmtUsd(c.agreedRate)}</p>
                          <p className="text-xs text-muted-foreground">{label(c.bookingState)}</p>
                        </>
                      ) : (
                        <span className="text-muted-foreground">None</span>
                      )}
                    </TableCell>
                    <TableCell className={`${cell} pr-6`}>
                      <p className="line-clamp-2 text-sm">{c.summary || <span className="text-muted-foreground">No closing notes recorded</span>}</p>
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

// "DRY_VAN / TX / GA" from the service, as a rep would say it.
function lane(search: string | null): string {
  if (!search) return "Not recorded";
  const [equipment, from, to] = search.split(" / ");
  return `${label(equipment)}, ${from ?? "any"} to ${to ?? "any"}`;
}

function CallSheet({ call: c }: { call: Call }) {
  return (
    <DetailSheet
      trigger={<span className="font-sans font-medium tabular-nums">{fmtShort(c.startedAt)}</span>}
      title={
        <span className="flex items-center gap-3">
          Call <StatusPill code={c.outcome} />
        </span>
      }
      description={c.summary || "No closing notes recorded."}
    >
      {c.recordingUrl && <a href={c.recordingUrl} target="_blank" rel="noopener noreferrer" className="text-sm font-medium underline">Open recording and transcript in HappyRobot</a>}
      <SheetSection title="Call">
        <Facts
          items={[
            ["First activity", fmtTime(c.startedAt)],
            ["Closed", fmtTime(c.closedAt)],
            ["Carrier", na(c.carrierName)],
            ["MC", na(c.mc)],
            ["Email code verified", c.verifiedAt ? fmtTime(c.verifiedAt) : c.codePassed ? "Earlier in the call" : "No"],
            ["Lane asked", lane(c.search)],
            ["Agent counteroffers", fmtCount(c.counters ?? null)],
            ["Pricing rounds used", fmtCount(c.rounds)],
            ["Outcome", label(c.outcome)],
            ["Call ID", <span key="id" className="font-mono text-xs">{c.id}</span>],
          ]}
        />
      </SheetSection>
      <SheetSection title="Agreement">
        {c.bookingLoadId ? (
          <Facts
            items={[
              ["Load", <span key="l" className="font-mono">{c.bookingLoadId}</span>],
              ["Opening offer", fmtUsd(c.openingRate)],
              ["Agreed rate", fmtUsd(c.agreedRate)],
              ["Booking", <StateBadge key="s" state={c.bookingState} />],
            ]}
          />
        ) : (
          <p className="text-sm text-muted-foreground">No agreement recorded on this call.</p>
        )}
      </SheetSection>
      <SheetSection title={`Activity (${c.events.length})`}>
        <EventList events={c.events} />
      </SheetSection>
    </DetailSheet>
  );
}
