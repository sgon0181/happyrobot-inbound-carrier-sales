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
import { RepQueue } from "@/components/rep-queue";
import { CallLog } from "@/components/call-log";
import { TurnedAway } from "@/components/turned-away";
import { fmtCount, label } from "@/lib/format";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { requireAppUser } from "@/lib/auth";
import {
  describeFailure,
  getSnapshot,
  type Kpis,
} from "@/lib/ops-service";

export const dynamic = "force-dynamic";

const PAGE_TITLE = "Carrier Sales";

function toMs(v: string | null): number {
  const t = v === null ? Number.NaN : Date.parse(v);
  return Number.isNaN(t) ? Number.NEGATIVE_INFINITY : t;
}
function newestFirst<T>(rows: T[], at: (r: T) => string | null): T[] {
  return [...rows].sort((a, b) => toMs(at(b)) - toMs(at(a)));
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
  const snapshotTime = result.ok ? Date.parse(result.snapshot.generatedAt ?? "") : 0;
  const now = Number.isFinite(snapshotTime) ? snapshotTime : 0;

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
            description="The carrier agreed and nothing has been sent. Confirm sends once to the TMS; Decline releases this reservation."
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
        {outcomes.length === 0 ? <span>none yet</span> : outcomes.map(([name, n]) => <Badge key={name} variant="outline">{label(name)}: {n}</Badge>)}
        <span className="ml-2 flex items-center gap-1"><IconFlask className="size-3" /> Test calls, excluded: {fmtCount(kpis.syntheticCalls)}</span>
      </div>
    </section>
  );
}
