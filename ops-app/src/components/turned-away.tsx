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
import type { Lane } from "@/lib/snapshot";
import { label, na } from "@/lib/format";
export function TurnedAway({ lanes }: { lanes: Lane[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Unmatched demand</CardTitle>
        <CardDescription>
          Latest unmatched lane per real recorded call. This is demand, not
          measured revenue.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {["Equipment", "From", "To", "Recorded calls"].map((h) => (
                  <TableHead key={h}>{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {!lanes.length ? (
                <TableRow>
                  <TableCell colSpan={4}>
                    No unmatched demand recorded.
                  </TableCell>
                </TableRow>
              ) : (
                lanes.map((l) => (
                  <TableRow
                    key={`${l.equipment}-${l.originState}-${l.destState}`}
                  >
                    <TableCell>{label(l.equipment)}</TableCell>
                    <TableCell>{na(l.originState)}</TableCell>
                    <TableCell>{na(l.destState)}</TableCell>
                    <TableCell>{l.calls}</TableCell>
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
