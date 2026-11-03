import { IconLock, IconSend } from "@tabler/icons-react";

// Always visible: whether a rep's Confirm can reach the TMS right now.
export function SendMode({ liveBooking }: { liveBooking: boolean | null }) {
  const on = liveBooking === true;
  return (
    <div
      role="status"
      className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm ${on ? "border-status-act/40 bg-status-act/8" : "bg-card"}`}
    >
      <span className={`[&>svg]:size-4 ${on ? "text-status-act" : "text-muted-foreground"}`}>{on ? <IconSend /> : <IconLock />}</span>
      <span className="font-medium">
        {on ? "Booking sends on" : liveBooking === false ? "Booking sends off" : "Booking send mode unavailable"}
      </span>
      <span className="text-muted-foreground">
        {on
          ? "Confirm sends one request to the TMS. There is no supported cancellation."
          : "Confirm is disabled. Decline and read-only reconciliation remain available."}
      </span>
    </div>
  );
}
