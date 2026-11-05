"use client";

import { useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { IconRefresh } from "@tabler/icons-react";

import { Button } from "@/components/ui/button";
import { fmtTime } from "@/lib/format";

const EVERY_MS = 15_000; // a pending transition blocks the next refresh

// Re-renders the page from a fresh snapshot while the tab is visible, so new reservations
// appear and time-dependent actions, such as Reconcile after a minute, are recomputed.
export function AutoRefresh({ generatedAt }: { generatedAt: string | null }) {
  const router = useRouter();
  const [paused, setPaused] = useState(false);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    if (paused || pending) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") startTransition(() => router.refresh());
    }, EVERY_MS);
    return () => window.clearInterval(timer);
  }, [paused, pending, router]);

  const shown = generatedAt ? `Snapshot ${fmtTime(generatedAt)}` : "No snapshot";
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span>{shown}, {pending ? "refresh in progress" : paused ? "auto-refresh paused" : "refresh every 15 s"}</span>
      <Button size="sm" variant="outline" disabled={pending} onClick={() => startTransition(() => router.refresh())}>
        <IconRefresh data-icon="inline-start" />
        {pending ? "Refreshing" : "Refresh"}
      </Button>
      <Button size="sm" variant="ghost" onClick={() => setPaused(!paused)}>
        {paused ? "Resume" : "Pause"}
      </Button>
    </div>
  );
}
