import {
  IconAlertTriangle,
  IconCircleCheck,
  IconFlask,
  IconHandStop,
  IconPhoneCall,
  IconShieldCheck,
  IconTarget,
  IconTruckDelivery,
  IconTruckOff,
  IconUserCheck,
} from "@tabler/icons-react";

import { AppShell } from "@/components/app-shell";
import { RepActions } from "@/components/rep-actions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { requireAppUser } from "@/lib/auth";
import {
  allowedActions,
  CALLER_CONSENT_REVIEW,
  describeFailure,
  getSnapshot,
  type CallRow,
  type Kpis,
  type QueueRow,
} from "@/lib/ops-service";

export const dynamic = "force-dynamic";

const PAGE_TITLE = "Carrier Sales Prototype";
const cell = "py-3 text-left";

function fmtTime(v: string | number | null): string {
  if (v === null) return "n/a";
  const d = typeof v === "number" ? new Date(v < 1e12 ? v * 1000 : v) : new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return `${d.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}
const fmtCount = (n: number | null) => (n === null ? "n/a" : Math.round(n).toLocaleString("en-US"));
const fmtUsd = (n: number | null) => (n === null ? "n/a" : `$${Math.round(n).toLocaleString("en-US")}`);
const na = (v: string | null | undefined) => (v ? v : "n/a");

const DECISION_LABEL = { awaiting: "Awaiting rep", confirmed: "Rep confirmed", declined: "Rep declined" } as const;

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

  return (
    <AppShell title={PAGE_TITLE}>
      <Alert>
        <IconAlertTriangle />
        <AlertTitle>Prototype</AlertTitle>
        <AlertDescription>
          Data and rep actions go through the carrier sales service. A rep decision is recorded by the service;
          booking status in the TMS is shown exactly as the TMS reports it.
        </AlertDescription>
      </Alert>

      {!result.ok ? (
        <Alert variant="destructive">
          <AlertTitle>Snapshot unavailable</AlertTitle>
          <AlertDescription>Carrier sales service: {describeFailure(result)}.</AlertDescription>
        </Alert>
      ) : (
        <>
          <KpiOverview kpis={result.snapshot.kpis} queue={result.snapshot.queue} status={result.snapshot.status} />
          <RepQueue rows={result.snapshot.queue.filter((r) => r.cohort === "real")} title="Rep queue: real" />
          <RepQueue
            rows={result.snapshot.queue.filter((r) => r.cohort !== "real")}
            title="Rep queue: synthetic"
            description="Test bookings. Kept separate from real results."
          />
          <CallLog calls={result.snapshot.calls.filter((c) => c.cohort === "real")} title="Call log: real" />
          <CallLog calls={result.snapshot.calls.filter((c) => c.cohort !== "real")} title="Call log: synthetic" />
        </>
      )}
    </AppShell>
  );
}

function KpiOverview({ kpis, queue, status }: { kpis: Kpis; queue: QueueRow[]; status: string | null }) {
  const syntheticQueue = queue.filter((r) => r.cohort !== "real").length;
  return (
    <>
      <section className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-medium">Real cohort</h2>
          {status ? <span className="text-xs text-muted-foreground">Service status: {status}</span> : null}
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile icon={<IconTarget />} label="Northstar" value={kpis.northstar === null ? "n/a" : kpis.northstar.toFixed(2)} description="Acknowledged handoffs per code-passed real call, as reported by the service." />
          <StatTile icon={<IconPhoneCall />} label="Real calls" value={fmtCount(kpis.realCalls)} description="Answered calls from real carriers." />
          <StatTile icon={<IconShieldCheck />} label="Code-passed calls" value={fmtCount(kpis.codePassedCalls)} description="Real calls that passed carrier verification." />
          <StatTile icon={<IconHandStop />} label="Acknowledged handoffs" value={fmtCount(kpis.acknowledgedHandoffs)} description="Tentative bookings acknowledged for rep handoff." />
          <StatTile icon={<IconTruckDelivery />} label="TMS confirmed" value={fmtCount(kpis.tmsConfirmed)} description="Bookings the TMS reports as confirmed." />
          <StatTile icon={<IconUserCheck />} label="Rep confirmed" value={fmtCount(kpis.repConfirmed)} description="Rep approvals recorded. Not the same as TMS confirmation." />
          <StatTile icon={<IconAlertTriangle />} label="Unknown TMS state" value={fmtCount(kpis.unknown)} description="Bookings needing reconcile with the TMS." />
          <StatTile icon={<IconTruckOff />} label="Unmet demand" value={fmtCount(kpis.unmetDemand)} description="Requests with no matching load." />
        </div>
      </section>
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium">Synthetic cohort</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile icon={<IconFlask />} label="Synthetic calls" value={fmtCount(kpis.syntheticCalls)} description="Test calls. Excluded from real results." />
          <StatTile icon={<IconCircleCheck />} label="Synthetic queue rows" value={fmtCount(syntheticQueue)} description="Test bookings in the rep queue." />
        </div>
      </section>
    </>
  );
}

function RepQueue({ rows, title, description }: { rows: QueueRow[]; title: string; description?: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>
          {description ?? "Confirm is offered only for acknowledged or TMS-confirmed bookings awaiting a rep. Unknown TMS state offers Reconcile or Decline and review."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="max-h-[32rem] min-h-0 overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-card">
              <TableRow className="border-dashed">
                {["Load", "MC", "Rate", "Booking state", "TMS status", "Reference", "Rep decision", "Rep", "Review", "Reason", "Created", "Actions"].map((h) => (
                  <TableHead key={h} className={cell}>{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow className="border-dashed">
                  <TableCell className={cell} colSpan={12}>No bookings.</TableCell>
                </TableRow>
              ) : (
                rows.map((r) => (
                  <TableRow key={r.id} className="border-dashed">
                    <TableCell className={`${cell} font-mono text-xs`}>{na(r.loadId)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(r.mc)}</TableCell>
                    <TableCell className={`${cell} tabular-nums`}>{fmtUsd(r.rate)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(r.state)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(r.tmsStatus)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(r.reference)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{r.repDecision ? DECISION_LABEL[r.repDecision] : "n/a"}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{na(r.rep)}</TableCell>
                    <TableCell className={cell}>
                      {r.reviewRequired ? <Badge variant="destructive">Review</Badge> : <span className="text-xs text-muted-foreground">No</span>}
                    </TableCell>
                    <TableCell className={`${cell} max-w-60 whitespace-normal text-xs`}>
                      {r.reason?.trim() === CALLER_CONSENT_REVIEW ? (
                        <span className="font-medium text-destructive">
                          Caller consent review: the caller did not explicitly agree to book this load. Do not confirm.
                        </span>
                      ) : (
                        na(r.reason)
                      )}
                    </TableCell>
                    <TableCell className={`${cell} text-xs`}>{fmtTime(r.createdAt)}</TableCell>
                    <TableCell className={cell}>
                      <RepActions
                        bookingId={r.id}
                        actions={allowedActions(r)}
                        declineLabel={r.state === "UNKNOWN" ? "Decline and review" : "Decline"}
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

function CallLog({ calls, title }: { calls: CallRow[]; title: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Transcripts are redacted for verification codes, pricing figures and identifiers.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="max-h-[40rem] min-h-0 overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-card">
              <TableRow className="border-dashed">
                {["Started", "Carrier", "MC", "Outcome", "Rounds", "Code passed", "Closed", "Transcript"].map((h) => (
                  <TableHead key={h} className={cell}>{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {calls.length === 0 ? (
                <TableRow className="border-dashed">
                  <TableCell className={cell} colSpan={8}>No calls.</TableCell>
                </TableRow>
              ) : (
                calls.map((c) => (
                  <TableRow key={c.id} className="border-dashed align-top">
                    <TableCell className={`${cell} text-xs`}>{fmtTime(c.startedAt)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{na(c.carrierName)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(c.mc)}</TableCell>
                    <TableCell className={`${cell} font-mono text-xs`}>{na(c.outcome)}</TableCell>
                    <TableCell className={`${cell} tabular-nums`}>{fmtCount(c.rounds)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{c.codePassedAt === null ? "No" : fmtTime(c.codePassedAt)}</TableCell>
                    <TableCell className={`${cell} text-xs`}>{fmtTime(c.closedAt)}</TableCell>
                    <TableCell className={`${cell} max-w-[28rem] whitespace-normal text-xs`}>
                      {c.transcript ? (
                        <div className="flex flex-col gap-1">
                          {c.transcript.summary ? <p>{c.transcript.summary}</p> : null}
                          {c.transcript.notes ? <p className="text-muted-foreground">Notes: {c.transcript.notes}</p> : null}
                          <p className="text-muted-foreground">
                            {[
                              c.transcript.sentiment ? `Sentiment: ${c.transcript.sentiment}` : null,
                              c.transcript.source ? `Source: ${c.transcript.source}` : null,
                              c.transcript.summarySource ? `Summary by: ${c.transcript.summarySource}` : null,
                              c.transcript.complete === null ? null : c.transcript.complete ? "Complete" : "Partial",
                              c.transcript.tools.length ? `Tools: ${c.transcript.tools.join(", ")}` : null,
                            ].filter(Boolean).join(" | ")}
                          </p>
                          {c.transcript.transcript ? (
                            <details>
                              <summary className="cursor-pointer">Transcript</summary>
                              <pre className="mt-1 max-h-64 overflow-auto font-sans whitespace-pre-wrap">{c.transcript.transcript}</pre>
                            </details>
                          ) : null}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">Not available</span>
                      )}
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
