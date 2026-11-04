import type { Call } from "@/lib/snapshot";
import { demoVoiceRunIds, missedVoiceRunId } from "@/lib/demo-voice-runs";

export const groupTitles = {
  recorded: "Recorded calls",
  verified: "Email verified",
  matched: "Load matched",
  reserved: "Reservation created",
  unmatched: "Verified without a match",
  "no-agreement": "Matched without an agreement",
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

export function performance(calls: Call[]) {
  // The platform inventory defines the cohort. Twin's deployment tag serves a different purpose.
  const completed = calls.filter((c) => demoVoiceRunIds.has(c.id));
  const uniqueCalls = new Map(completed.map((c) => [c.id, c]));
  const recorded = [...uniqueCalls.values()];
  const verified = recorded.filter((c) => c.codePassed);
  const matched = verified.filter((c) => c.foundMatch);
  const reserved = verified.filter((c) => c.bookingLoadId !== null);
  const paired = reserved.filter((c) => concession(c) !== null);
  const groups: Record<Group, Call[]> = {
    recorded, verified, matched, reserved, paired,
    unmatched: verified.filter((c) => !c.foundMatch && c.bookingLoadId === null),
    "no-agreement": matched.filter((c) => c.bookingLoadId === null),
  };
  return {
    groups,
    completedCount: demoVoiceRunIds.size,
    sessionCount: new Set([...demoVoiceRunIds, missedVoiceRunId]).size,
    conversion: verified.length ? Math.round(100 * reserved.length / verified.length) : null,
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
