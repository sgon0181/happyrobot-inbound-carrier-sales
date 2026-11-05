import Link from "next/link";
import { CallLog } from "@/components/call-log";
import { recordHref } from "@/lib/views";
import { fmtShort } from "@/lib/format";
import { concession, groupHref, groupTitles, usd, type Group, type Performance } from "@/lib/performance";

const steps: [Group, Group | null][] = [
  ["recorded", null], ["authority-attempted", "recorded"], ["authority-passed", "authority-attempted"],
  ["issued", "authority-passed"], ["verified", "issued"], ["matched", "verified"], ["reserved", "matched"],
];
export function dateRange(report: Performance) {
  const dates = report.groups.recorded.map(c => Date.parse(c.sessionAt ?? ""))
    .filter(Number.isFinite).sort((a, b) => a - b);
  if (!dates.length) return "Dates not recorded";
  const format = new Intl.DateTimeFormat("en-US", {month:"short", day:"numeric", year:"numeric", timeZone:"America/Chicago"});
  return `${format.format(dates[0])} to ${format.format(dates[dates.length - 1])} (CT)`;
}

const focus = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";
const panel = "rounded-xl border bg-card text-card-foreground";

function Sample({ report }: { report: Performance }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <div>
        <p className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">All recorded calls</p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">Carrier sales performance</h2>
      </div>
      <p className="text-sm text-muted-foreground">{dateRange(report)} · All voice versions</p>
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
        <p className="mt-3 text-sm text-muted-foreground">Carrier and agent agreed on a load and rate for a rep to review. Includes calls still in progress.</p>
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
      <h3 className="font-semibold">Qualification and load matching</h3>
      <p className="mt-1 text-sm text-muted-foreground">Calls reaching each stage, as a share of the prior stage.</p>
      <div className="mt-4 space-y-1">
        {steps.map(([step, previous]) => {
          const count = groups[step].length;
          const denominator = previous ? groups[previous].length : 0;
          return (
            <Link key={step} href={groupHref(step)} className={`grid grid-cols-[minmax(7.5rem,1.5fr)_1fr_5rem] items-center gap-3 rounded py-1 text-sm hover:bg-muted/40 ${focus}`}>
              <span>{groupTitles[step]}</span>
              <span className="h-2 overflow-hidden rounded-full bg-muted" aria-hidden="true">
                <span className="block h-full rounded-full bg-teal-700 dark:bg-teal-400" style={{ width: `${previous ? (denominator ? Math.min(100, 100 * count / denominator) : 0) : (count ? 100 : 0)}%` }} />
              </span>
              <strong className="text-right tabular-nums">{count} {previous && <span className="font-normal text-muted-foreground">/ {denominator}</span>}</strong>
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
      <p className="mt-1 text-sm text-muted-foreground">Only calls with end evidence appear in these loss groups.</p>
      <div className="mt-3 divide-y">
        {(["unmatched", "no-agreement"] as const).map((key) => (
          <Link key={key} href={groupHref(key)} className={`flex items-center gap-3 py-3 text-sm hover:underline ${focus}`}>
            <span className="w-8 text-xl font-semibold tabular-nums">{groups[key].length}</span>
            <span>{groupTitles[key]}</span><span aria-hidden="true" className="ml-auto text-muted-foreground">›</span>
          </Link>
        ))}
      </div>
      <Link href={groupHref("unresolved")} className={`block border-t py-3 text-sm hover:underline ${focus}`}>{groups.unresolved.length} verified calls are ongoing or missing end evidence.</Link>
      <div className="border-t py-3 text-sm"><strong>Agreement after a match</strong>
        <p>{groups.matched.length ? Math.round(100 * groups.matched.filter(c => c.bookingLoadId !== null).length / groups.matched.length) + "%" : "No rate yet"} · {groups.matched.filter(c => c.bookingLoadId !== null).length} of {groups.matched.length} matched calls reached a reservation, including calls in progress.</p>
      </div>
      <div className="border-t pt-3">
        <Link href={groupHref("final-limit")} className={`text-sm font-semibold hover:underline ${focus}`}>{groups["final-limit"].length} exhausted the final offer</Link>
        <p className="mt-1 text-xs text-muted-foreground">Among <Link className="underline" href={groupHref("negotiated")}>{groups.negotiated.length} calls that reached negotiation</Link>. Review the recorded price decisions.</p>
      </div>
    </section>
  );
}

function sessionTime(seconds: number | null) {
  if (seconds === null) return "Not recorded";
  const rounded = Math.round(seconds);
  return `${Math.floor(rounded / 60)}m ${rounded % 60}s`;
}

export function PerformanceOverview({ report }: { report: Performance }) {
  const latest = [...report.groups.reserved].sort((a, b) => (b.sessionAt ?? "").localeCompare(a.sessionAt ?? ""))[0];
  return (
    <section className="space-y-4">
      <Sample report={report} />
      <Headline report={report} />
      <div className="grid gap-4 lg:grid-cols-[1.25fr_1fr]">
        <Funnel groups={report.groups} /><LostCalls groups={report.groups} />
      </div>
      <div className={`${panel} flex flex-wrap items-center justify-between gap-3 px-5 py-3`}>
        <div className="text-sm"><strong>Median call duration</strong><span className="ml-2">{sessionTime(report.medianSeconds)} where duration is recorded · {sessionTime(report.medianReservedSeconds)} on agreements</span></div>
        {latest && <Link href={recordHref("reservations", latest.bookingLoadId, latest.id)} className="text-sm font-semibold underline underline-offset-4">Review latest agreement · {latest.bookingLoadId}</Link>}
      </div>
      <p className="text-xs text-muted-foreground">{report.sessionCount} recorded calls across voice versions. {report.completedCount} have end evidence. {report.missedCount > 0 && <>{report.missedCount} are marked missed in the native inventory. </>} Durations are available for {report.durationCount} calls. These development calls repeat carriers. {report.topCarrierCount > 0 && <>{report.topCarrierCount} of {report.groups.reserved.length} agreements belong to the most frequent recorded MC.</>}</p>
    </section>
  );
}

export function PerformanceRecords({ report, group }: { report: Performance; group: Group }) {
  const rows = report.groups[group];
  const agreements = report.groups.reserved;
  const unknown = agreements.filter(c => c.counters == null || c.counters > 3).length;
  return (
    <section className="min-w-0 space-y-4">
      <Link href="/?view=overview" className="text-sm font-medium underline underline-offset-4">Back to performance</Link>
      <p className="text-sm text-muted-foreground">All recorded calls · {dateRange(report)}</p>
      {group === "unmatched" && <div className={panel + " p-5"}>
        <h2 className="font-semibold">Why no match was recorded</h2>
        <p className="mt-2 text-sm">{rows.filter(c => c.noMatchSeen).length} had an empty search · {rows.filter(c => !c.searchAttempted).length} never reached search · {rows.filter(c => c.searchAttempted && !c.noMatchSeen).length} had a different search outcome.</p>
      </div>}
      {group === "paired" && <div className={`${panel} overflow-x-auto p-4`}>
        <h2 className="font-semibold">Counteroffers before agreement</h2>
        <p className="mt-1 text-sm text-muted-foreground">Agent counteroffers across {agreements.length} reservations. Accepting the carrier’s first ask uses zero counteroffers.</p>
        <dl className="my-3 grid grid-cols-2 gap-2 border-y py-3 sm:grid-cols-4">
          {[0, 1, 2, 3].map(n => <div key={n}><dt className="text-sm">{n} counteroffer{n === 1 ? "" : "s"}</dt><dd className="font-semibold">{agreements.filter(c => c.counters === n).length} calls</dd></div>)}
        </dl>
        {unknown > 0 && <p className="mb-2 text-xs text-muted-foreground">Unclassified counteroffer history: {unknown}.</p>}
        <h2 className="mb-3 font-semibold">Price pairs by call</h2>
        <table className="w-full text-left text-sm tabular-nums">
          <thead><tr className="border-b text-muted-foreground">{["Call", "Load", "Opening", "Agreed", "Change"].map((name) => <th className="py-2 pr-3" key={name}>{name}</th>)}</tr></thead>
          <tbody>{rows.map((c) => <tr className="border-b last:border-0" key={c.id}>
            <td className="py-2 pr-3">{fmtShort(c.startedAt)}</td><td className="pr-3"><Link href={recordHref("reservations", c.bookingLoadId, c.id)} className="underline">{c.bookingLoadId}</Link></td>
            <td>{usd(c.openingRate)}</td><td>{usd(c.agreedRate)}</td><td>{usd(concession(c))}</td>
          </tr>)}</tbody>
        </table>
      </div>}
      <CallLog title={groupTitles[group]} calls={rows} />
    </section>
  );
}
