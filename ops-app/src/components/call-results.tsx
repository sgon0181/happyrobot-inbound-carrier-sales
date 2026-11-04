import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Call, Kpis } from "@/lib/snapshot";
import { fmtCount } from "@/lib/format";

// Historical milestones count calls, including reservations subsequently released.
// Test history is useful for review, but is never presented as business performance.
export function CallResults({ calls, kpis }: { calls: Call[]; kpis: Kpis | null }) {
  const counts: [string, number | null, string][] = [
    ["Calls recorded", kpis ? kpis.calls : calls.length, "Saved call records, not an answer rate"],
    ["Email code verified", kpis ? kpis.codePassed : calls.filter((c) => c.codePassed).length, "Calls that passed a code at least once"],
    ["Reservations created", kpis ? kpis.handoffs : calls.filter((c) => c.bookingLoadId).length, "Historical agreements, including later releases"],
  ];
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>{kpis ? "Recorded call results" : "Test call results"}</CardTitle>
        <CardDescription>
          {kpis ? "Real calls, all recorded history. Test calls excluded." : "Test calls, all recorded history. Excluded from business performance."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5 py-5">
        {kpis ? <Conversion kpis={kpis} /> : null}
        <div className="grid gap-4 sm:grid-cols-3">
          {counts.map(([name, value, hint]) => (
            <div key={name} className="rounded-lg border p-4">
              <p className="text-sm font-medium">{name}</p>
              <p className="mt-1 text-2xl font-semibold tabular-nums">{fmtCount(value)}</p>
              <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">Counts are calls, not distinct carriers. A reservation is not a final TMS booking.</p>
        {kpis ? <Diagnostics kpis={kpis} /> : null}
      </CardContent>
    </Card>
  );
}

function Conversion({ kpis: k }: { kpis: Kpis }) {
  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg bg-muted/60 p-4">
      <p className="text-3xl font-semibold tabular-nums">{k.northstar === null ? "No rate yet" : `${Math.round(k.northstar * 100)}%`}</p>
      <div>
        <h3 className="text-sm font-semibold">Reservation conversion after email verification</h3>
        <p className="mt-1 text-sm">
          {fmtCount(k.handoffs)} of {fmtCount(k.codePassed)} email-verified calls created a reservation.
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {k.codePassed === 0 ? "No email-verified calls recorded yet." : "Small demo sample. This is not a production conversion estimate."}
        </p>
      </div>
    </div>
  );
}

function Diagnostics({ kpis: k }: { kpis: Kpis }) {
  return (
    <details className="border-t pt-3 text-xs text-muted-foreground">
      <summary className="cursor-pointer font-medium">Recording coverage and service timing</summary>
      <dl className="mt-3 grid gap-x-6 gap-y-2 sm:grid-cols-2">
        <div><dt>End reports received</dt><dd>{fmtCount(k.endsReported)} calls</dd></div>
        <div><dt>Closing notes saved</dt><dd>{fmtCount(k.closedWithSummary)} calls</dd></div>
        <div><dt>Historically approved for submission</dt><dd>{fmtCount(k.repConfirmed)} reservations, including later failed submissions</dd></div>
        <div><dt>Time to first load match</dt><dd>{k.medianSecondsToFirstOffer === null ? "Not recorded" : `${Math.round(k.medianSecondsToFirstOffer)} s`}, median from first service activity, excluding greeting and speech</dd></div>
      </dl>
      <p className="mt-3">{fmtCount(k.syntheticCalls)} test calls excluded. Calls that reach neither a service action nor a saved end report are not counted.</p>
    </details>
  );
}
