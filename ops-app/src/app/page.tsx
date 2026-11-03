import { AppShell } from "@/components/app-shell";
import { SendMode } from "@/components/send-mode";
import { AutoRefresh } from "@/components/auto-refresh";
import { ReceiptPanels } from "@/components/receipt-panels";
import { RepQueue } from "@/components/rep-queue";
import { CallLog } from "@/components/call-log";
import { TurnedAway, lanesFrom } from "@/components/turned-away";
import { Attention, Funnel, KpiStrip, Outcomes, attention } from "@/components/overview";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { requireAppUser } from "@/lib/auth";
import { describeFailure, getSnapshot } from "@/lib/ops-service";
import type { Booking, Call, Snapshot } from "@/lib/snapshot";
import { VIEW_TITLE, readView, type Scope, type View } from "@/lib/views";

export const dynamic = "force-dynamic";

const PAGE_TITLE = "Carrier Sales";
const SUBTITLE: Record<View, string> = {
  overview: "What needs a rep, and where calls stop",
  reservations: "Agreed by the carrier, nothing sent yet",
  bookings: "Sent once, with the TMS reply as returned",
  calls: "Every recorded call and its outcome",
  demand: "Lanes carriers wanted that we could not cover",
};

type Params = Promise<Record<string, string | string[] | undefined>>;

function toMs(v: string | null): number {
  const t = v === null ? Number.NaN : Date.parse(v);
  return Number.isNaN(t) ? Number.NEGATIVE_INFINITY : t;
}
function newestFirst<T>(rows: T[], at: (r: T) => string | null): T[] {
  return [...rows].sort((a, b) => toMs(at(b)) - toMs(at(a)));
}
const inScope = (scope: Scope) => (row: { cohort: string | null }) =>
  scope === "real" ? row.cohort === "real" : row.cohort !== "real";

export default async function HomePage({ searchParams }: { searchParams?: Params } = {}) {
  // Sign-in is verified with the platform before the service is called.
  await requireAppUser();
  const { view, scope } = readView((await searchParams) ?? {});
  const result = await getSnapshot();
  const snapshotTime = result.ok ? Date.parse(result.snapshot.generatedAt ?? "") : 0;
  const now = Number.isFinite(snapshotTime) ? snapshotTime : 0;
  const bookings = result.ok ? newestFirst(result.snapshot.bookings.filter(inScope(scope)), (b) => b.updatedAt) : [];
  const calls = result.ok ? newestFirst(result.snapshot.calls.filter(inScope(scope)), (c) => c.startedAt) : [];
  const waiting = bookings.filter((b) => b.state === "RESERVED");

  return (
    <AppShell
      title={view === "overview" ? PAGE_TITLE : `${PAGE_TITLE} · ${VIEW_TITLE[view]}`}
      subtitle={SUBTITLE[view]}
      view={view}
      scope={scope}
      counts={{ reservations: waiting.length }}
    >
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
          <SendMode liveBooking={result.snapshot.liveBooking} />
          <Page view={view} scope={scope} snapshot={result.snapshot} bookings={bookings} calls={calls} now={now} />
        </>
      )}
    </AppShell>
  );
}

function Page({
  view,
  scope,
  snapshot,
  bookings,
  calls,
  now,
}: {
  view: View;
  scope: Scope;
  snapshot: Snapshot;
  bookings: Booking[];
  calls: Call[];
  now: number;
}) {
  const live = snapshot.liveBooking;
  const waiting = bookings.filter((b) => b.state === "RESERVED");
  const sent = bookings.filter((b) => b.state !== "RESERVED");
  const lanes = scope === "real" ? snapshot.turnedAway : lanesFrom(calls);
  const queue = (
    <RepQueue
      title="Awaiting rep"
      description="The carrier agreed and nothing has been sent. Confirm sends once to the TMS; Decline releases this reservation."
      rows={waiting}
      now={now}
      liveBooking={live}
      empty="No reservations waiting for a rep."
    />
  );
  const sentTable = (
    <RepQueue
      title="Sent and closed"
      description="The TMS status and reference as the TMS returned them. PENDING is an acknowledgement, never a confirmation. UNKNOWN may have landed and is never resent."
      rows={sent}
      now={now}
      liveBooking={live}
      empty="No sent or closed bookings in this view."
    />
  );

  switch (view) {
    case "reservations":
      return queue;
    case "bookings":
      return sentTable;
    case "calls":
      return <CallLog title={scope === "real" ? "Calls" : "Test calls"} calls={calls} />;
    case "demand":
      return <TurnedAway lanes={lanes} />;
    default:
      return (
        <>
          <KpiStrip kpis={snapshot.kpis} />
          <div className="grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
            <Attention items={attention(bookings, calls, now, scope)} />
            <Funnel calls={calls} bookings={bookings} />
          </div>
          {queue}
          <div className="grid gap-5 xl:grid-cols-2">
            <Outcomes calls={calls} />
            <TurnedAway lanes={lanes} />
          </div>
        </>
      );
  }
}
