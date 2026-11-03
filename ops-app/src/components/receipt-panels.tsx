"use client";

import { useSyncExternalStore } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { dropReceipt, getReceipts, getServerReceipts, subscribe } from "@/lib/unsaved-receipts";

// A send whose receipt Twin never took. The bytes exist only here and in the service log,
// so they stay on screen, above every table and whatever the snapshot does, until dismissed.
export function ReceiptPanels() {
  const receipts = useSyncExternalStore(subscribe, getReceipts, getServerReceipts);
  const entries = Object.entries(receipts);
  if (entries.length === 0) return null;
  return (
    <section className="flex flex-col gap-3">
      {entries.map(([loadId, receipt]) => (
        <UnsavedReceipt key={loadId} loadId={loadId} receipt={receipt} />
      ))}
    </section>
  );
}

function UnsavedReceipt({ loadId, receipt }: { loadId: string; receipt: string }) {
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
  function dismiss() {
    if (window.confirm("Dismiss this receipt? Make sure it is copied or downloaded first.")) dropReceipt(loadId);
  }
  return (
    <div className="flex flex-col gap-2 rounded-md border border-destructive p-3 text-xs">
      <p className="font-medium text-destructive">
        {loadId} was sent, but its receipt was not saved. Keep this copy: it is every byte the TMS returned. Never resend.
      </p>
      <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all font-mono">{receipt}</pre>
      <div className="flex gap-2">
        <Button size="sm" variant="outline" onClick={copy}>Copy</Button>
        <Button size="sm" variant="outline" onClick={download}>Download</Button>
        <Button size="sm" variant="ghost" onClick={dismiss}>Dismiss</Button>
      </div>
    </div>
  );
}
