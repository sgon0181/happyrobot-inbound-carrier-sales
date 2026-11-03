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
import type { Call } from "@/lib/snapshot";
import { fmtCount, fmtTime, fmtUsd, label, na } from "@/lib/format";
const cell = "py-3 text-left align-top whitespace-normal";
export function CallLog({ title, calls }: { title: string; calls: Call[] }) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>
          Stored service activity, not a verbatim conversation or proof of a
          completed transfer.
        </CardDescription>
      </CardHeader>
      <CardContent className="min-w-0">
        <div className="max-h-[40rem] w-full min-w-0 overflow-auto">
          <Table className="min-w-[1000px]">
            <TableHeader className="sticky top-0 bg-card">
              <TableRow>
                {[
                  "First recorded (CT)",
                  "Carrier",
                  "Code passed",
                  "Last search",
                  "Rounds",
                  "Outcome",
                  "Agreement",
                  "Notes and timeline",
                ].map((h) => (
                  <TableHead key={h}>{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {!calls.length ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    No calls recorded in this view.
                  </TableCell>
                </TableRow>
              ) : (
                calls.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className={cell}>
                      {fmtTime(c.startedAt)}
                    </TableCell>
                    <TableCell className={cell}>
                      {na(c.carrierName)}
                      <p>MC {na(c.mc)}</p>
                    </TableCell>
                    <TableCell className={cell}>
                      {c.verifiedAt
                        ? fmtTime(c.verifiedAt)
                        : "Not currently verified"}
                    </TableCell>
                    <TableCell className={cell}>{na(c.search)}</TableCell>
                    <TableCell className={cell}>{fmtCount(c.rounds)}</TableCell>
                    <TableCell className={cell}>{label(c.outcome)}</TableCell>
                    <TableCell className={cell}>
                      {c.bookingLoadId ? (
                        <>
                          {c.bookingLoadId}
                          <p>{fmtUsd(c.agreedRate)}</p>
                          <StateBadge state={c.bookingState} />
                        </>
                      ) : (
                        "No agreement recorded"
                      )}
                    </TableCell>
                    <TableCell className={`${cell} min-w-72 max-w-md`}>
                      <p>{c.summary || "No closing notes recorded"}</p>
                      <details>
                        <summary className="cursor-pointer underline">
                          Activity ({c.events.length})
                        </summary>
                        <EventList events={c.events} />
                      </details>
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
