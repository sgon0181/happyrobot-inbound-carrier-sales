import Link from "next/link";
import { CallLog } from "@/components/call-log";
import { fmtShort } from "@/lib/format";
import { concession, groupHref, groupTitles, usd, type Group, type Performance } from "@/lib/performance";

const steps: Group[] = ["recorded", "verified", "matched", "reserved"];
const dateRange = "November 2 to 4, 2026";
const focus = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";
const panel = "rounded-xl border bg-card text-card-foreground";

function Sample() {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <div>
        <p className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">Recorded demo calls</p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">Carrier sales performance</h2>
      </div>
      <p className="text-sm text-muted-foreground">{dateRange} · Multiple workflow versions</p>
    </div>
  );
}

function Headline({ report }: { report: Performance }) {
  const { groups, conversion, medianConcession } = report;
  return (
    <div className={`${panel} grid divide-y md:grid-cols-[1.25fr_1fr] md:divide-x md:divide-y-0`}>
      <Link href={groupHref("reserved")} className={`rounded-xl p-5 hover:bg-muted/30 sm:p-6 ${focus}`}>
        <h3 className="text-sm font-semibold">Verified calls with a reservation</h3>
        <div className="mt-3 flex flex-wrap items-baseline gap-3">
          <span className="text-4xl font-semibold tracking-tight tabular-nums sm:text-5xl">{conversion === null ? "No rate yet" : `${conversion}%`}</span>
          <span className="text-base font-medium tabular-nums">{groups.reserved.length} of {groups.verified.length} verified calls</span>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">Carrier and agent agreed on a load and rate for a rep to review.</p>
      </Link>
      <Link href={groupHref("paired")} className={`rounded-xl p-5 hover:bg-muted/30 sm:p-6 ${focus}`}>
        <h3 className="text-sm font-semibold">Rate above opening offer</h3>
        <div className="mt-3 flex flex-wrap items-baseline gap-3">
          <span className="text-4xl font-semibold tracking-tight tabular-nums sm:text-5xl">{usd(medianConcession)}</span>
          <span className="text-base font-medium">median per agreement</span>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">Opening and agreed rates available for {groups.paired.length} of {groups.reserved.length} agreements.</p>
      </Link>
    </div>
  );
}

function Funnel({ groups }: { groups: Performance["groups"] }) {
  return (
    <div className={`${panel} p-5 sm:p-6`}>
      <h3 className="font-semibold">Call outcomes</h3>
      <p className="mt-1 text-sm text-muted-foreground">Select a stage to review its calls.</p>
      <div className="mt-4 space-y-1">
        {steps.map((step) => {
          const count = groups[step].length;
          return (
            <Link key={step} href={groupHref(step)} className={`grid grid-cols-[minmax(7.5rem,1fr)_1.3fr_2rem] items-center gap-3 rounded py-2 text-sm hover:bg-muted/40 ${focus}`}>
              <span>{groupTitles[step]}</span>
              <span className="h-2 overflow-hidden rounded-full bg-muted" aria-hidden="true">
                <span className="block h-full rounded-full bg-teal-700 dark:bg-teal-400" style={{ width: `${groups.recorded.length ? 100 * count / groups.recorded.length : 0}%` }} />
              </span>
              <strong className="text-right tabular-nums">{count}</strong>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function LostCalls({ groups }: { groups: Performance["groups"] }) {
  return (
    <section className={`${panel} p-5 sm:p-6`}>
      <h3 className="font-semibold">Where verified calls stopped</h3>
      <p className="mt-1 text-sm text-muted-foreground">Open a group to inspect the lane or the negotiation.</p>
      <div className="mt-3 divide-y">
        {(["unmatched", "no-agreement"] as const).map((key) => (
          <Link key={key} href={groupHref(key)} className={`flex items-center gap-3 py-3 text-sm hover:underline ${focus}`}>
            <span className="w-8 text-xl font-semibold tabular-nums">{groups[key].length}</span>
            <span>{groupTitles[key]}</span><span aria-hidden="true" className="ml-auto text-muted-foreground">›</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

export function PerformanceOverview({ report }: { report: Performance }) {
  return (
    <section className="space-y-4">
      <Sample />
      <Headline report={report} />
      <div className="grid gap-4 lg:grid-cols-[1.25fr_1fr]">
        <Funnel groups={report.groups} /><LostCalls groups={report.groups} />
      </div>
      <p className="text-xs text-muted-foreground">{report.sessionCount} inbound demo sessions. HappyRobot marked {report.completedCount} completed and one missed. Twin has records for {report.groups.recorded.length} completed calls.</p>
    </section>
  );
}

export function PerformanceRecords({ report, group }: { report: Performance; group: Group }) {
  const rows = report.groups[group];
  return (
    <section className="min-w-0 space-y-4">
      <Link href="/" className="text-sm font-medium underline underline-offset-4">Back to performance</Link>
      <p className="text-sm text-muted-foreground">Recorded demo calls · {dateRange}</p>
      {group === "paired" && <div className={`${panel} overflow-x-auto p-4`}>
        <h2 className="mb-3 font-semibold">Price pairs by call</h2>
        <table className="w-full text-left text-sm tabular-nums">
          <thead><tr className="border-b text-muted-foreground">{["Call", "Load", "Opening", "Agreed", "Change"].map((name) => <th className="py-2 pr-3" key={name}>{name}</th>)}</tr></thead>
          <tbody>{rows.map((c) => <tr className="border-b last:border-0" key={c.id}>
            <td className="py-2 pr-3">{fmtShort(c.startedAt)}</td><td className="pr-3">{c.bookingLoadId}</td>
            <td>{usd(c.openingRate)}</td><td>{usd(c.agreedRate)}</td><td>{usd(concession(c))}</td>
          </tr>)}</tbody>
        </table>
      </div>}
      <CallLog title={groupTitles[group]} calls={rows} />
    </section>
  );
}
