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
import type { Call, Lane } from "@/lib/snapshot";
import { label, na } from "@/lib/format";

// Attribute only the last explicit empty search. Legacy ambiguous requests share an unknown bucket.
export function lanesFrom(calls: Call[]): Lane[] {
  const counts = new Map<string, Lane>();
  for (const c of calls) {
    if (!c.codePassed || !c.noMatchSeen || c.foundMatch || c.bookingLoadId) continue;
    const key = c.noMatchLane ?? "";
    const [equipment, originState, destState] = key ? key.split(" / ") : [null, null, null];
    const lane = counts.get(key) ?? { equipment, originState, destState, calls: 0 };
    lane.calls += 1;
    counts.set(key, lane);
  }
  return [...counts.values()].sort((a, b) => b.calls - a.calls);
}

export function TurnedAway({ lanes }: { lanes: Lane[] }) {
  const top = Math.max(1, ...lanes.map((l) => l.calls));
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="border-b py-4">
        <CardTitle>Unmatched demand <span className="ml-1 font-normal text-muted-foreground tabular-nums">{lanes.length}</span></CardTitle>
        <CardDescription>One call per last explicit empty search, excluding later matches. Ambiguous legacy lanes show as not recorded.</CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        <Table className="table-fixed">
          <TableHeader className="bg-muted/70">
            <TableRow>
              {[["Equipment", "w-[28%] pl-6"], ["From", "w-[14%]"], ["To", "w-[14%]"], ["Calls", "pr-6"]].map(([h, w]) => (
                <TableHead key={h} className={`${w} px-3 text-xs text-muted-foreground`}>{h}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {!lanes.length ? (
              <TableRow>
                <TableCell colSpan={4} className="px-6 py-8 text-center text-muted-foreground">No unmatched demand recorded.</TableCell>
              </TableRow>
            ) : (
              lanes.map((l) => (
                <TableRow key={JSON.stringify([l.equipment, l.originState, l.destState])}>
                  <TableCell className="px-3 pl-6">{label(l.equipment)}</TableCell>
                  <TableCell className="px-3">{na(l.originState)}</TableCell>
                  <TableCell className="px-3">{na(l.destState)}</TableCell>
                  <TableCell className="px-3 pr-6">
                    <span className="flex items-center gap-3">
                      <span className="h-1.5 w-full max-w-48 overflow-hidden rounded-full bg-muted">
                        <span className="block h-full rounded-full bg-foreground/70" style={{ width: `${Math.round((l.calls / top) * 100)}%` }} />
                      </span>
                      <span className="tabular-nums">{l.calls}</span>
                    </span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
