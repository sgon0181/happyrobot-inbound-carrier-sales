import { isRunId } from "@/lib/views";
import type { Call } from "@/lib/snapshot";
import { demoVoiceRunIds, missedVoiceRunId, nativeDuration } from "@/lib/demo-voice-runs";

export const groupTitles = {
  recorded: "Recorded calls",
  "authority-attempted": "Authority checked",
  "authority-passed": "Operating authority passed",
  issued: "Email code issued",
  verified: "Email verification passed",
  matched: "Load matched",
  reserved: "Reservation created",
  unmatched: "Ended without a match",
  unresolved: "Verified calls without end evidence",
  "no-agreement": "Ended after matching without agreement",
  negotiated: "Reached negotiation",
  "final-limit": "Final offer exhausted",
  paired: "Opening and agreed rates",
} as const;

export type Group = keyof typeof groupTitles;
export function readGroup(value: string | string[] | undefined): Group | null {
  return typeof value === "string" && Object.hasOwn(groupTitles, value) ? value as Group : null;
}
export const groupHref = (group: Group) => `/?group=${group}`;

export function concession(call: Call): number | null {
  if (call.openingRate === null || call.agreedRate === null) return null;
  return call.agreedRate - call.openingRate;
}

function median(values: number[]): number | null {
  const sorted = values.sort((a, b) => a - b);
  if (!sorted.length) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function duration(call: Call): number | null {
  const native = nativeDuration.get(call.id);
  if (native !== undefined) return native;
  const seconds = call.durationSeconds;
  return typeof seconds === "number" && Number.isFinite(seconds) && seconds >= 0 ? seconds : null;
}

function hasEnded(call: Call): boolean {
  return Boolean(call.endedAt || call.closedAt || demoVoiceRunIds.has(call.id));
}

export function performance(calls: Call[]) {
  // Native inventory enriches evidence; it never limits which workflow versions count.
  const nativeCalls = calls.filter((c) => isRunId(c.id));
  const uniqueCalls = new Map(nativeCalls.map((c) => [c.id, c]));
  const recorded = [...uniqueCalls.values()];
  const verified = recorded.filter((c) => c.codePassed);
  const matched = verified.filter((c) => c.foundMatch);
  const reserved = verified.filter((c) => c.bookingLoadId !== null);
  const paired = reserved.filter((c) => concession(c) !== null);
  const groups: Record<Group, Call[]> = {
    recorded, verified, matched, reserved, paired,
    "authority-attempted": recorded.filter((c) => c.authorityAttempted),
    "authority-passed": recorded.filter((c) => c.authorityPassed),
    issued: recorded.filter((c) => c.codeIssued),
    negotiated: recorded.filter((c) => c.negotiated),
    "final-limit": recorded.filter((c) => c.finalLimit && c.bookingLoadId === null),
    unmatched: verified.filter((c) => hasEnded(c) && !c.foundMatch && c.bookingLoadId === null),
    unresolved: verified.filter((c) => !hasEnded(c)),
    "no-agreement": matched.filter((c) => hasEnded(c) && c.bookingLoadId === null),
  };
  const counts = new Map<string, number>();
  for (const c of reserved) if (c.mc) counts.set(c.mc, (counts.get(c.mc) ?? 0) + 1);
  return {
    topCarrierCount: Math.max(0, ...counts.values()),
    groups,
    completedCount: recorded.filter(c => hasEnded(c) && c.id !== missedVoiceRunId).length,
    sessionCount: recorded.length,
    missedCount: recorded.filter(c => c.id === missedVoiceRunId).length,
    durationCount: recorded.filter(c => duration(c) !== null).length,
    conversion: verified.length ? Math.round(100 * reserved.length / verified.length) : null,
    medianSeconds: median(recorded.flatMap((c) => duration(c) ?? [])),
    medianReservedSeconds: median(reserved.flatMap((c) => duration(c) ?? [])),
    medianConcession: median(paired.flatMap((c) => concession(c) ?? [])),
  };
}
export type Performance = ReturnType<typeof performance>;

export function usd(amount: number | null): string {
  if (amount === null) return "No rate yet";
  return amount.toLocaleString("en-US", {
    style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 2,
  });
}
