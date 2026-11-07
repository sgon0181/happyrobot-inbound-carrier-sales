import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { SendMode } from "@/components/send-mode";
import { AutoRefresh } from "@/components/auto-refresh";
import { ReceiptPanels } from "@/components/receipt-panels";
import { RepQueue } from "@/components/rep-queue";
import { CallLog } from "@/components/call-log";
import { Attention, attention } from "@/components/overview";
import { DemandReport } from "@/components/demand-report";
import { ReservationReview } from "@/components/reservation-review";
import { RecordSearch, filterBookings, filterCalls, type Filters } from "@/components/record-search";
import { ReservationSummary } from "@/components/current-desk";
import { PerformanceOverview, PerformanceRecords } from "@/components/performance";
import { performance, readGroup } from "@/lib/performance";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { canManageBookings } from "@/lib/rep-access";
import { requireAppUser } from "@/lib/auth";
import { describeFailure, getSnapshot } from "@/lib/ops-service";
import type { Booking, Call, Snapshot } from "@/lib/snapshot";
import { VIEW_TITLE, isRunId, readView, workspaceFilters, type View } from "@/lib/views";

export const dynamic = "force-dynamic";
const subtitle: Record<View, string> = {
  reservations: "Review the agreement before submitting a booking",
  overview: "Inbound carrier sales performance",
  bookings: "Submission status and TMS receipts",
  calls: "Carrier requests, prices and call history",
  demand: "Freight requested by verified carriers",
};
type Params = Promise<Record<string, string | string[] | undefined>>;
type Props = { view: View; filters: Filters; snapshot: Snapshot; canManage: boolean; calls: Call[]; bookings: Booking[]; now: number };

function workRows(snapshot: Snapshot) {
  // Include every recorded workflow run. Deployment tags do not hide call history.
  const calls = snapshot.calls.filter(c => isRunId(c.id))
    .sort((a, b) => (b.sessionAt ?? "").localeCompare(a.sessionAt ?? ""));
  const byId = new Map(calls.map(c => [c.id, c.sessionAt ?? ""]));
  const time = (b: Booking) => (b.callId && byId.get(b.callId)) || b.updatedAt || "";
  const bookings = snapshot.bookings.filter(b => !b.callId || isRunId(b.callId))
    .sort((a, b) => time(b).localeCompare(time(a)));
  return { calls, bookings };
}

export default async function HomePage({ searchParams }: { searchParams?: Params } = {}) {
  const { user } = await requireAppUser();
  const params = (await searchParams) ?? {};
  const view = readView(params);
  const result = await getSnapshot();
  const rows = result.ok ? workRows(result.snapshot) : { calls: [], bookings: [] };
  const time = result.ok ? Date.parse(result.snapshot.generatedAt ?? "") : 0;
  const group = readGroup(params.group);
  const report = result.ok && view === "overview" ? performance(rows.calls) : null;
  return <AppShell title={VIEW_TITLE[view]} subtitle={subtitle[view]} view={view}
    counts={{ reservations: rows.calls.filter(c => c.bookingLoadId !== null).length }}
    actions={<AutoRefresh generatedAt={result.ok ? result.snapshot.generatedAt : null} />}>
    <ReceiptPanels />
    {!result.ok ? <Alert variant="destructive"><AlertTitle>Snapshot unavailable</AlertTitle>
      <AlertDescription>Carrier sales service: {describeFailure(result)}. Retrying every 15 seconds.</AlertDescription></Alert>
      : report ? (group ? <PerformanceRecords group={group} report={report} /> : <>
        <PerformanceOverview report={report} />
        <ReservationSummary bookings={rows.bookings} now={Number.isFinite(time) ? time : 0} />
      </>)
      : <Workspace canManage={canManageBookings(user.sub)} filters={workspaceFilters(params)} view={view} snapshot={result.snapshot} {...rows} now={Number.isFinite(time) ? time : 0} />}
  </AppShell>;
}

function Review({ filters, bookings, calls, now, snapshot, canManage }: Props) {
  const b = bookings.find(b => b.loadId === filters.load && (!filters.run || filters.run === b.callId));
  const c = calls.find(c => c.id === (b?.callId ?? filters.run) && c.bookingLoadId === filters.load);
  return <ReservationReview canManage={canManage} booking={b} call={c} now={now} live={snapshot.liveBooking} sandboxMc={snapshot.sandboxBookingMc} />;
}

function BookingList({ view, bookings, calls, filters, now, snapshot }: Props) {
  const pending = view === "reservations";
  const history = pending && filters.bucket !== "awaiting";
  const list = bookings.filter(b => pending ? b.state === "RESERVED" : b.state !== "RESERVED");
  const byRun = new Map(calls.map(c => [c.id, c]));
  const prior = calls.filter(c => Boolean(c.bookingLoadId));
  const filtered = filterBookings(list, filters, byRun);
  const urgent = pending ? [] : attention(list, [], now).filter(i => i.code === "SUBMITTING" || i.code === "UNKNOWN");
  const historyRows = filterCalls(prior, { ...filters, status: "" }).filter(c => !filters.status || c.bookingState === filters.status);
  return <>
    {urgent.length > 0 && <Attention title="Submission exceptions" items={urgent} />}
    {pending && <nav aria-label="Reservation lists" className="flex flex-wrap items-center gap-4 text-sm">
      <Link aria-current={!history ? "page" : undefined} className={history ? "text-muted-foreground underline" : "font-semibold"} href="/?view=reservations&bucket=awaiting">Awaiting rep ({list.length})</Link>
      <Link aria-current={history ? "page" : undefined} className={history ? "font-semibold" : "text-muted-foreground underline"} href="/?view=reservations">All reservations ({prior.length})</Link>
    </nav>}
    <p className="text-xs text-muted-foreground">All recorded calls and voice versions · New service records appear as calls arrive.</p>
    <RecordSearch view={view} filters={filters} statuses={history ? prior.map(c => c.bookingState) : list.map(b => b.state)} />
    {history ? <CallLog title="All reservations" calls={historyRows} /> : <RepQueue title={pending ? "Awaiting rep review" : "Booking and release history"}
      description={pending ? "Open the originating call and check the agreed rate. Latest calls appear first." : "Inspect the TMS response, reference and submission history."}
      rows={filtered} callById={byRun} now={now} liveBooking={snapshot.liveBooking} empty="No records match these filters." />}
    <SendMode liveBooking={snapshot.liveBooking} sandboxMc={snapshot.sandboxBookingMc} />
  </>;
}

function Workspace(props: Props) {
  const { view, filters, calls } = props;
  if (view === "reservations" || view === "bookings") return filters.load ? <Review {...props} /> : <BookingList {...props} />;
  if (view === "demand") return <DemandReport calls={calls} bucket={filters.bucket} />;
  return <>
    <RecordSearch view="calls" filters={filters} statuses={[...calls.map(c => c.outcome), "missing_close"]} />
    <CallLog title="Recorded calls" calls={filterCalls(calls, filters)} />
    <p className="text-xs text-muted-foreground">{calls.length} recorded calls across all voice versions. New service calls appear as activity is recorded.</p>
  </>;
}
