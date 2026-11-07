import { IconLock, IconSend } from "@tabler/icons-react";

// Always visible: whether a rep's Confirm can reach the TMS right now.
export function SendMode({ liveBooking, sandboxMc = null }: { liveBooking: boolean | null; sandboxMc?: string | null }) {
  const sandbox = liveBooking === false && sandboxMc !== null;
  const on = liveBooking === true || sandbox;
  return (
    <div
      role="status"
      className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm ${on ? "border-status-act/40 bg-status-act/8" : "bg-card"}`}
    >
      <span className={`[&>svg]:size-4 ${on ? "text-status-act" : "text-muted-foreground"}`}>{on ? <IconSend /> : <IconLock />}</span>
      <span className="font-medium">
        {sandbox ? "Challenge sandbox sends" : on ? "Booking sends on" : liveBooking === false ? "Booking sends off" : "Booking send mode unavailable"}
      </span>
      <span className="text-muted-foreground">
        {sandbox
          ? `Rep Confirm sends once to the challenge TMS for demo MC ${sandboxMc}. Demo inbox access does not prove carrier identity. Live booking remains off.`
          : on
          ? "Confirm sends one request to the TMS. There is no supported cancellation."
          : "Confirm is disabled. Decline and read-only reconciliation remain available."}
      </span>
    </div>
  );
}
