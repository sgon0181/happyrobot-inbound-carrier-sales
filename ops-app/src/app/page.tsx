import {
  IconAlertTriangle,
  IconClock,
  IconFlask,
  IconHandStop,
  IconPhoneCall,
  IconShieldCheck,
  IconTarget,
  IconTruckDelivery,
  IconUserCheck,
} from "@tabler/icons-react";

import { AppShell } from "@/components/app-shell";
import { AutoRefresh } from "@/components/auto-refresh";
import { ReceiptPanels } from "@/components/receipt-panels";
import { RepActions } from "@/components/rep-actions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { requireAppUser } from "@/lib/auth";
import {
  allowedActions,
  describeFailure,
  getSnapshot,
  type Booking,
  type Call,
  type EventRow,
  type Kpis,
  type Lane,
} from "@/lib/ops-service";

export const dynamic = "force-dynamic";

const PAGE_TITLE = "HappyRobot Logistics Carrier Sales";
const cell = "py-3 text-left";

function toMs(v: string | null): number {
  const t = v === null ? Number.NaN : Date.parse(v);
  return Number.isNaN(t) ? Number.NEGATIVE_INFINITY : t;
}
function newestFirst<T>(rows: T[], at: (r: T) => string | null): T[] {
  return [...rows].sort((a, b) => toMs(at(b)) - toMs(at(a)));
}
function fmtTime(v: string | null): string {
  if (v === null) return "n/a";
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? v : `${d.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}
const fmtCount = (n: number | null) => (n === null ? "n/a" : Math.round(n).toLocaleString("en-US"));
const fmtUsd = (n: number | null) => (n === null ? "n/a" : `$${Math.round(n).toLocaleString("en-US")}`);
const na = (v: string | null | undefined) => (v ? v : "n/a");

// Colour by meaning: a TMS reference is good news, FAILED is bad, UNKNOWN needs review.
const STATE_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  RESERVED: "default",
  SUBMITTING: "secondary",
  ACK_PENDING: "secondary",
  CONFIRMED: "default",
  UNKNOWN: "destructive",
  FAILED: "destructive",
  RELEASED: "outline",
};

function StateBadge({ state }: { state: string | null }) {
  if (!state) return <span className="text-xs text-muted-foreground">n/a</span>;
  return <Badge variant={STATE_BADGE[state] ?? "outline"}>{state}</Badge>;
}

function StatTile({ icon, label, value, description }: { icon: React.ReactNode; label: string; value: string; description: string }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="[&>svg]:size-4">{icon}</span>
          {label}
        </div>
        <div className="text-3xl font-semibold tabular-nums">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

export default async function HomePage() {
  // Sign-in is verified with the platform before the service is called.
  await requireAppUser();
  const result = await getSnapshot();
  const now = Date.now();

  return (
    <AppShell title={PAGE_TITLE}>
      {/* Outside the snapshot's success branch, so a failed snapshot keeps both. */}
      <div className="flex justify-end">
        <AutoRefresh generatedAt={result.ok ? result.snapshot.generatedAt : null} />
      </div>
      <ReceiptPanels />
      {!result.ok ? (
        <Alert variant="destructive">
          <AlertTitle>Snapshot unavailable</AlertTitle>
          <AlertDescription>
            Carrier sales service: {describeFailure(result)}. The page keeps retrying every 15 seconds.
          </AlertDescription>
        </Alert>
      ) : (
        <>
          <Overview kpis={result.snapshot.kpis} />
          <RepQueue
            title="Reservations awaiting a rep"
            description="The carrier agreed and nothing has been sent. Confirm sends one booking to the TMS, which spends the load; Decline frees it."
            rows={newestFirst(result.snapshot.bookings.filter((b) => b.cohort === "real" && b.state === "RESERVED"), (b) => b.updatedAt)}
            now={now}
          />
          <RepQueue
            title="Sent and closed bookings"
            description="The TMS status and reference as the TMS returned them. PENDING is an acknowledgement, never a confirmation. UNKNOWN may have landed and is never resent."
            rows={newestFirst(result.snapshot.bookings.filter((b) => b.cohort === "real" && b.state !== "RESERVED"), (b) => b.updatedAt)}
            now={now}
          />
          <CallLog title="Call log" calls={newestFirst(result.snapshot.calls.filter((c) => c.cohort === "real"), (c) => c.startedAt)} />
          <TurnedAway lanes={result.snapshot.turnedAway} />
          <RepQueue
            title="Test bookings"
            description="Synthetic calls. Kept out of every KPI above."
            rows={newestFirst(result.snapshot.bookings.filter((b) => b.cohort !== "real"), (b) => b.updatedAt)}
            now={now}
          />
          <CallLog title="Test calls" calls={newestFirst(result.snapshot.calls.filter((c) => c.cohort !== "real"), (c) => c.startedAt)} />
        </>
      )}
    </AppShell>
  );
}

function Overview({ kpis }: { kpis: Kpis }) {
  const outcomes = Object.entries(kpis.outcomes).sort((a, b) => b[1] - a[1]);
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-medium">Real calls</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile icon={<IconTarget />} label="Northstar" value={kpis.northstar === null ? "n/a" : `${Math.round(kpis.northstar * 100)}%`} description="Reserved handoffs per code-passed call: the leg the agent owns." />
        <StatTile icon={<IconPhoneCall />} label="Calls answered" value={fmtCount(kpis.calls)} description="Real carrier calls, every one answered." />
        <StatTile icon={<IconShieldCheck />} label="Code passed" value={fmtCount(kpis.codePassed)} description="Calls with an eligible MC and a passed emailed code." />
        <StatTile icon={<IconHandStop />} label="Reserved handoffs" value={fmtCount(kpis.handoffs)} description="Calls that reached a rep with a reservation." />
        <StatTile icon={<IconUserCheck />} label="Rep confirmed" value={fmtCount(kpis.repConfirmed)} description="Reservations a rep sent to the TMS." />
        <StatTile icon={<IconTruckDelivery />} label="TMS acknowledged" value={fmtCount(kpis.tmsAcknowledged)} description={`Reference with PENDING. TMS confirmed (BOOKED): ${fmtCount(kpis.tmsConfirmed)}.`} />
        <StatTile icon={<IconAlertTriangle />} label="Unknown" value={fmtCount(kpis.unknown)} description="Sends that may have landed. Reconcile; never resend." />
        <StatTile icon={<IconClock />} label="Time to first offer" value={kpis.medianSecondsToFirstOffer === null ? "n/a" : `${Math.round(kpis.medianSecondsToFirstOffer)} s`} description="Median, from the call's first request to its first offer." />
      </div>
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>Outcomes:</span>
        {outcomes.length === 0 ? <span>none yet</span> : outcomes.map(([name, n]) => <Badge key={name} variant="outline">{name}: {n}</Badge>)}
        <span className="ml-2 flex items-center gap-1"><IconFlask className="size-3" /> Test calls, excluded: {fmtCount(kpis.syntheticCalls)}</span>
      </div>
    </section>
  );
}

function EventList({ events }: { events: EventRow[] }) {
  if (events.length === 0) return null;
  return (
    <details>
      <summary className="cursor-pointer text-muted-foreground">Events ({events.length})</summary>
      <ol className="mt-1 flex flex-col gap-0.5 font-mono">
        {events.map((e, i) => (
          <li key={`${e.seq ?? i}`}>
            {fmtTime(e.at).slice(11, 16)} {na(e.action)} {[e.status, e.state, e.reason, e.rep].filter(Boolean).join(" ")}
            {e.detail ? <span className="text-muted-foreground"> ({e.detail})</span> : null}
          </li>
        ))}
      </ol>
    </details>
  );
}

function RepQueue({ title, description, rows, now }: { title: string; description: string; rows: Booking[]; now: number }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="max-h-[32rem] min-h-0 overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-card">
              <TableRow className="border-dashed">
                {["Load", "MC", "Rate", "State", "TMS status", "Reference", "Rep", "Reason", "Updated", "Evidence", "Actions"].map((h) => (
                  <TableHead key={h} className={cell}>{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow className="border-dashed">
                  <TableCell className={cell} colSpan={11}>None.</TableCell>
                </TableRow>
              ) : (
                rows.map((b) => (
                  <TableRow key={b.loadId} className="border-dashed align-top">
                    <TableCell className={`${cell} font-mono text-xs`}>{b.loadId}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(b.mc)}</TableCell>
                    <TableCell className={`${cell} tabular-nums`}>{fmtUsd(b.rate)}</TableCell>
                    <TableCell className={cell}><StateBadge state={b.state} /></TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(b.tmsStatus)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(b.reference)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{na(b.rep)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{na(b.reason)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{fmtTime(b.updatedAt)}</TableCell>
                    <TableCell className={`${cell} max-w-60 whitespace-normal text-xs`}>
                      {b.sendStep ? (
                        <p className="font-mono">
                          {b.sendStep}{b.sendError ? ` ${b.sendError}` : ""}, {fmtCount(b.sendBytes)} bytes, sha256 {b.sendSha256?.slice(0, 12)}
                        </p>
                      ) : null}
                      <EventList events={b.events} />
                    </TableCell>
                    <TableCell className={cell}>
                      <RepActions
                        loadId={b.loadId}
                        version={b.version}
                        actions={allowedActions(b, now)}
                        confirmText={`Send the booking for ${b.loadId}, MC ${na(b.mc)}, at ${fmtUsd(b.rate)} to the TMS? This spends the load and cannot be undone.`}
                      />
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

function CallLog({ title, calls }: { title: string; calls: Call[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Each call&apos;s outcome, derived when read, with its events: the audit trail of MCs, loads, offers, rounds and agreed rates.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="max-h-[40rem] min-h-0 overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-card">
              <TableRow className="border-dashed">
                {["Started", "Carrier", "MC", "Code passed", "Asked for", "Rounds", "Outcome", "Booking", "Summary"].map((h) => (
                  <TableHead key={h} className={cell}>{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {calls.length === 0 ? (
                <TableRow className="border-dashed">
                  <TableCell className={cell} colSpan={9}>No calls.</TableCell>
                </TableRow>
              ) : (
                calls.map((c) => (
                  <TableRow key={c.id} className="border-dashed align-top">
                    <TableCell className={`${cell} text-xs`}>{fmtTime(c.startedAt)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{na(c.carrierName)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(c.mc)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{c.verifiedAt ? fmtTime(c.verifiedAt) : "No"}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{na(c.search)}</TableCell>
                    <TableCell className={`${cell} tabular-nums`}>{fmtCount(c.rounds)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(c.outcome)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>
                      {c.bookingLoadId ? (
                        <span className="flex flex-col gap-1">
                          <span className="font-mono">{c.bookingLoadId} {fmtUsd(c.agreedRate)}</span>
                          <StateBadge state={c.bookingState} />
                        </span>
                      ) : "n/a"}
                    </TableCell>
                    <TableCell className={`${cell} max-w-[28rem] whitespace-normal text-xs`}>
                      {c.summary ? <p>{c.summary}</p> : <span className="text-muted-foreground">No summary</span>}
                      <EventList events={c.events} />
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

function TurnedAway({ lanes }: { lanes: Lane[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Turned-away demand</CardTitle>
        <CardDescription>Lanes real carriers asked for when nothing matched: freight the brokerage could not cover.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-dashed">
              {["Equipment", "From", "To", "Calls"].map((h) => (
                <TableHead key={h} className={cell}>{h}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {lanes.length === 0 ? (
              <TableRow className="border-dashed">
                <TableCell className={cell} colSpan={4}>None.</TableCell>
              </TableRow>
            ) : (
              lanes.map((l) => (
                <TableRow key={`${l.equipment}-${l.originState}-${l.destState}`} className="border-dashed">
                  <TableCell className={`${cell} font-mono text-xs`}>{na(l.equipment)}</TableCell>
                  <TableCell className={`${cell} font-mono text-xs`}>{na(l.originState)}</TableCell>
                  <TableCell className={`${cell} font-mono text-xs`}>{na(l.destState)}</TableCell>
                  <TableCell className={`${cell} tabular-nums`}>{l.calls}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
