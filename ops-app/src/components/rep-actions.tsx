"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { ActionReply, RepAction } from "@/lib/ops-service";

const LABEL: Record<RepAction, string> = { confirm: "Confirm", decline: "Decline", reconcile: "Reconcile" };
const RECEIPT_KEY = (loadId: string) => `unsaved-receipt:${loadId}`;

// Browser storage can be missing or refuse; the panel still shows for this page's life.
function stored(loadId: string): string | null {
  try {
    return window.localStorage.getItem(RECEIPT_KEY(loadId));
  } catch {
    return null;
  }
}
function store(loadId: string, receipt: string | null) {
  try {
    if (receipt === null) window.localStorage.removeItem(RECEIPT_KEY(loadId));
    else window.localStorage.setItem(RECEIPT_KEY(loadId), receipt);
  } catch {
    // nothing more to do: the panel holds the receipt until dismissed
  }
}

// A send whose receipt Twin never took. The bytes exist only here and in the service log,
// so they stay on screen, and in this browser, until the rep has copied or saved them.
function UnsavedReceipt({ loadId, receipt, onDismiss }: { loadId: string; receipt: string; onDismiss: () => void }) {
  async function copy() {
    try {
      await navigator.clipboard.writeText(receipt);
      toast.success("Receipt copied.");
    } catch {
      toast.error("Copy failed. Select the text and copy it, or download it.");
    }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([receipt], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `receipt-${loadId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className="mt-2 flex w-96 flex-col gap-2 rounded-md border border-destructive p-2 text-xs">
      <p className="font-medium text-destructive">
        Sent, but the receipt was not saved. Keep this copy: it is every byte the TMS returned. Never resend.
      </p>
      <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all font-mono">{receipt}</pre>
      <div className="flex gap-2">
        <Button size="sm" variant="outline" onClick={copy}>Copy</Button>
        <Button size="sm" variant="outline" onClick={download}>Download</Button>
        <Button size="sm" variant="ghost" onClick={onDismiss}>Dismiss</Button>
      </div>
    </div>
  );
}

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
        text: `Sent, but the receipt was not saved: ${r.state}, reference ${r.reference ?? "none"}. Keep the copy shown beside the booking.`,
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
  const [receipt, setReceipt] = useState<string | null>(null);

  useEffect(() => setReceipt(stored(loadId)), [loadId]);

  function keep(r: ActionReply) {
    const saved = JSON.stringify({ load_id: loadId, kept_at: new Date().toISOString(), ...r }, null, 2);
    store(loadId, saved);
    setReceipt(saved);
  }
  function dismiss() {
    if (!window.confirm("Dismiss this receipt? Make sure it is copied or downloaded first.")) return;
    store(loadId, null);
    setReceipt(null);
  }

  const panel = receipt ? <UnsavedReceipt loadId={loadId} receipt={receipt} onDismiss={dismiss} /> : null;
  if (actions.length === 0) {
    return (
      <div>
        <span className="text-xs text-muted-foreground">No action</span>
        {panel}
      </div>
    );
  }

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
        if (body.status === "receipt_not_saved") keep(body as ActionReply);
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
    <div>
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
      {panel}
    </div>
  );
}
