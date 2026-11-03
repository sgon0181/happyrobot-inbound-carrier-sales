"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { IconRefresh } from "@tabler/icons-react";

import { Button } from "@/components/ui/button";

const EVERY_MS = 15_000; // the service caches its snapshot for 5 seconds, so this costs little

// Re-renders the page from a fresh snapshot while the tab is visible, so new reservations
// appear and time-dependent actions, such as Reconcile after a minute, are recomputed.
export function AutoRefresh({ generatedAt }: { generatedAt: string | null }) {
  const router = useRouter();
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") router.refresh();
    }, EVERY_MS);
    return () => window.clearInterval(timer);
  }, [paused, router]);

  const at = generatedAt ? new Date(generatedAt) : null;
  const shown = at && !Number.isNaN(at.getTime()) ? at.toISOString().slice(11, 19) : "n/a";
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span>Snapshot {shown} UTC, {paused ? "auto-refresh paused" : "refreshing every 15 s"}</span>
      <Button size="sm" variant="outline" onClick={() => router.refresh()}>
        <IconRefresh data-icon="inline-start" />
        Refresh
      </Button>
      <Button size="sm" variant="ghost" onClick={() => setPaused(!paused)}>
        {paused ? "Resume" : "Pause"}
      </Button>
    </div>
  );
}
