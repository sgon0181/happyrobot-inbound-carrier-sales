import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function SendMode({ liveBooking }: { liveBooking: boolean | null }) {
  return <Alert>
    <AlertTitle>{liveBooking === true ? "Booking sends on" : liveBooking === false ? "Booking sends off" : "Booking send mode unavailable"}</AlertTitle>
    <AlertDescription>{liveBooking === true
      ? "Confirm sends one request to the TMS. There is no supported cancellation."
      : "Confirm is disabled. Decline and read-only reconciliation remain available."}</AlertDescription>
  </Alert>;
}
