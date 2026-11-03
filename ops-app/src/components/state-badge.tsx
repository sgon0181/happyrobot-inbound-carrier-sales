import { label } from "@/lib/format";
import { cn } from "@/lib/utils";

// One colour per meaning, so a rep can scan a column: act, wait, done, problem, inactive.
type Tone = "act" | "wait" | "done" | "problem" | "inactive";

const TONE: Record<string, Tone> = {
  RESERVED: "act",
  SUBMITTING: "wait",
  ACK_PENDING: "wait",
  CONFIRMED: "done",
  UNKNOWN: "problem",
  FAILED: "problem",
  RELEASED: "inactive",
  agreed_pending_rep: "act",
  in_progress: "wait",
  negotiation_failed: "inactive",
  no_match: "inactive",
  carrier_ineligible: "inactive",
  code_failed: "problem",
  ended_without_close: "problem",
  end_not_recorded: "problem",
  tms_unavailable: "problem",
  fmcsa_unavailable: "problem",
  pricing_review_required: "act",
};

const STYLE: Record<Tone, string> = {
  act: "bg-status-act/12 text-status-act [&>i]:bg-status-act",
  wait: "bg-status-wait/12 text-status-wait [&>i]:bg-status-wait",
  done: "bg-status-done/12 text-status-done [&>i]:bg-status-done",
  problem: "bg-status-problem/12 text-status-problem [&>i]:bg-status-problem",
  inactive: "bg-muted text-muted-foreground [&>i]:bg-muted-foreground/60",
};

export function StatusPill({ code, className }: { code: string | null; className?: string }) {
  const tone = TONE[code ?? ""] ?? "inactive";
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        STYLE[tone],
        className,
      )}
    >
      <i aria-hidden className="size-1.5 shrink-0 rounded-full" />
      <span className="truncate">{label(code)}</span>
    </span>
  );
}

export function StateBadge({ state }: { state: string | null }) {
  return <StatusPill code={state} />;
}
