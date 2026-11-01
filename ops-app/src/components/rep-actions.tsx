"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

type RepAction = "confirm" | "decline" | "reconcile";

const SUCCESS: Record<RepAction, string> = {
  confirm: "Rep confirmation recorded. TMS status is reported by the TMS.",
  decline: "Decline recorded and sent for review.",
  reconcile: "Reconcile requested. TMS status is reported by the TMS.",
};

export function RepActions({
  bookingId,
  actions,
  declineLabel,
}: {
  bookingId: string;
  actions: RepAction[];
  declineLabel: string;
}) {
  const router = useRouter();
  const [pending, setPending] = useState<RepAction | null>(null);

  if (actions.length === 0) return <span className="text-xs text-muted-foreground">No action</span>;

  async function submit(action: RepAction) {
    setPending(action);
    try {
      const response = await fetch(
        `/api/bookings/${encodeURIComponent(bookingId)}/${action}`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }
      );
      if (response.ok) {
        toast.success(SUCCESS[action]);
      } else {
        const body = (await response.json().catch(() => ({}))) as { error?: unknown };
        // Server messages are status-only by construction.
        toast.error(typeof body.error === "string" ? body.error : `Request failed (HTTP ${response.status})`);
      }
    } catch {
      toast.error("Request failed (no response)");
    } finally {
      setPending(null);
      router.refresh();
    }
  }

  const label: Record<RepAction, string> = { confirm: "Confirm", decline: declineLabel, reconcile: "Reconcile" };

  return (
    <div className="flex gap-2">
      {actions.map((action) => (
        <Button
          key={action}
          size="sm"
          variant={action === "confirm" ? "default" : "outline"}
          disabled={pending !== null}
          onClick={() => submit(action)}
        >
          {pending === action ? <Spinner data-icon="inline-start" /> : null}
          {label[action]}
        </Button>
      ))}
    </div>
  );
}
