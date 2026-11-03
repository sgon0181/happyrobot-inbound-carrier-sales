import { Badge } from "@/components/ui/badge";
import { label } from "@/lib/format";
const STATE_BADGE: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  RESERVED: "default",
  SUBMITTING: "secondary",
  ACK_PENDING: "secondary",
  CONFIRMED: "default",
  UNKNOWN: "destructive",
  FAILED: "destructive",
  RELEASED: "outline",
};
export function StateBadge({ state }: { state: string | null }) {
  return (
    <Badge variant={STATE_BADGE[state ?? ""] ?? "outline"}>
      {label(state)}
    </Badge>
  );
}
