"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { ActionReply, RepAction } from "@/lib/ops-service";
import { keepReceipt } from "@/lib/unsaved-receipts";

const LABEL: Record<RepAction, string> = { confirm: "Confirm", decline: "Decline", reconcile: "Reconcile" };
// What the service's status means for the rep. Unknown statuses are shown as they are.
function describe(r: ActionReply): { ok: boolean; text: string } {
  switch (r.status) {
    case "sent":
      return {
        ok: r.state === "ACK_PENDING" || r.state === "CONFIRMED",
        text: `Sent once. Booking ${r.state}, TMS status ${r.tmsStatus ?? "none"}, reference ${r.reference ?? "none"}${r.reason ? ` (${r.reason})` : ""}.`,
      };
    case "receipt_not_saved":
      return {
        ok: false,
        text: `Sent, but the receipt was not saved: ${r.state}, reference ${r.reference ?? "none"}. Keep the copy shown at the top of the page.`,
      };
    case "released":
      return { ok: true, text: "Reservation released. Nothing was sent, so the load is free." };
    case "reconciled":
      return { ok: true, text: `The TMS shows the load as ${r.loadStatus}. The booking is ${r.state}.` };
    case "failed":
      return { ok: false, text: `Not sent: ${r.reason}. The load is free; call the carrier back.` };
    case "stale":
      return { ok: false, text: "This booking changed since your screen loaded. Review it again." };
    case "not_allowed":
      return { ok: false, text: `Not available while the booking is ${r.state}.` };
    case "live_booking_off":
      return { ok: false, text: "Live booking is off, so nothing was sent to the TMS." };
    case "tms_unavailable":
      return { ok: false, text: "The TMS could not be read. Nothing was sent; try again." };
    case "too_early":
      return { ok: false, text: "The send started under a minute ago. Reconcile after a minute." };
    default:
      return { ok: false, text: `Service answered ${r.status}.` };
  }
}

export function RepActions({
  loadId,
  version,
  actions,
  confirmText,
}: {
  loadId: string;
  version: number;
  actions: RepAction[];
  confirmText: string;
}) {
  const router = useRouter();
  const [pending, setPending] = useState<RepAction | null>(null);

  if (actions.length === 0) return <span className="text-xs text-muted-foreground">No action</span>;

  async function submit(action: RepAction) {
    // A confirm sends LOAD_BOOK, which spends the load for good: ask once more.
    if (action === "confirm" && !window.confirm(confirmText)) return;
    setPending(action);
    try {
      const response = await fetch(`/api/bookings/${encodeURIComponent(loadId)}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version }),
      });
      const body = (await response.json().catch(() => ({}))) as Partial<ActionReply> & { error?: unknown };
      if (response.ok && typeof body.status === "string") {
        if (body.status === "receipt_not_saved") {
          // Kept in the page's shared store: this row may have moved or been replaced by now.
          const kept = { load_id: loadId, kept_at: new Date().toISOString(), ...body };
          keepReceipt(loadId, JSON.stringify(kept, null, 2));
        }
        const { ok, text } = describe(body as ActionReply);
        (ok ? toast.success : toast.error)(text, { duration: 15_000 });
      } else {
        // Server messages are status-only by construction.
        toast.error(typeof body.error === "string" ? body.error : `Request failed (HTTP ${response.status})`);
      }
    } catch {
      toast.error("Request failed (no response). Refresh before trying again.");
    } finally {
      setPending(null);
      router.refresh();
    }
  }

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
          {LABEL[action]}
        </Button>
      ))}
    </div>
  );
}
