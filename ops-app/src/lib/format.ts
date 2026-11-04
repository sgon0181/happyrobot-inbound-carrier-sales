// Display policy only. TMS units are assumed USD; source timestamps are assumed UTC.
export const MISSING = "Not recorded";
const central = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/Chicago",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
export function fmtTime(value: string | null): string {
  if (!value) return MISSING;
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return MISSING;
  const parts = Object.fromEntries(
    central.formatToParts(date).map((p) => [p.type, p.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute} CT`;
}
const centralShort = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/Chicago",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
// For dense table cells: "Nov 3, 16:50 CT". The full form stays in the side panel.
export function fmtShort(value: string | null): string {
  if (!value) return MISSING;
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return MISSING;
  const parts = Object.fromEntries(centralShort.formatToParts(date).map((p) => [p.type, p.value]));
  return `${parts.month} ${parts.day}, ${parts.hour}:${parts.minute} CT`;
}
export const fmtCount =(n: number | null) =>
  n === null ? MISSING : Math.round(n).toLocaleString("en-US");
export const fmtUsd = (n: number | null) =>
  n === null ? MISSING : `$${Math.round(n).toLocaleString("en-US")}`;
export const na = (v: string | null | undefined) => v || MISSING;

const LABELS: Record<string, string> = {
  RESERVED: "Awaiting rep",
  SUBMITTING: "Sending once",
  ACK_PENDING: "Sent, TMS pending",
  CONFIRMED: "TMS confirmed",
  UNKNOWN: "Send outcome unknown",
  FAILED: "Failed",
  RELEASED: "Released",
  PENDING: "Acknowledged, pending",
  BOOKED: "Confirmed by TMS",
  OPEN: "Open",
  agreed_pending_rep: "Reservation created",
  ended_without_agreement: "Ended without agreement",
  ended_without_close: "Ended, no closing notes",
  end_not_recorded: "End not recorded",
  caller_ended: "Historical inferred end",
  carrier_ineligible: "Carrier not eligible",
  code_failed: "Code check failed",
  no_match: "No matching load",
  tms_unavailable: "TMS unavailable",
  fmcsa_unavailable: "Authority service unavailable",
  pricing_review_required: "Pricing review needed",
  negotiation_failed: "Negotiation failed",
  in_progress: "In progress",
  DRY_VAN: "Dry van",
  REEFER: "Refrigerated",
  FLATBED: "Flatbed",
  STEP_DECK: "Step deck",
  POWER_ONLY: "Power only",
  verify_carrier: "Authority check",
  send_code: "Email code",
  verify_code: "Code check",
  find_loads: "Load search",
  negotiate: "Negotiation",
  close: "Closing notes",
  call_ended: "Call ended",
  eligible: "Authority passed",
  ineligible: "Not eligible",
  not_found: "MC not found",
  checking: "Checking",
  verified: "Code passed",
  sent: "Sent",
  send_failed: "Delivery failed",
  code_issued: "Code issued",
  found: "Matches returned",
  agreed: "Rate agreed",
  accepting: "Claiming reservation",
  counter: "Counter offered",
  final_offer: "Final offer",
  load_gone: "Load unavailable",
  ask_again: "Amount needs clarification",
  closed: "Closing recorded",
  ended: "End reported",
  reserved: "Reservation created",
  confirm: "Rep approved submission",
  decline: "Rep declined",
  reconcile: "TMS observation",
  reconciled: "TMS observation recorded",
  claim_voided: "Claim voided",
};
export function label(code: string | null | undefined): string {
  if (!code) return MISSING;
  return (
    LABELS[code] ??
    code.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase())
  );
}
export function nextAction(state: string | null): string {
  return (
    (
      {
        RESERVED: "Review terms, then confirm or decline.",
        SUBMITTING: "Wait for the send result.",
        ACK_PENDING: "Await TMS finalization; reconcile for an observation.",
        CONFIRMED: "TMS reports a final booking.",
        UNKNOWN: "Investigate and reconcile. Never resend.",
        FAILED: "Review the reason and contact the carrier.",
        RELEASED: "No booking sent for this reservation.",
      } as Record<string, string>
    )[state ?? ""] ?? "Review the recorded evidence."
  );
}

// FAILED covers both a pre-send refusal and a definite rejection from the TMS.
// A zero-length reply alone cannot prove that the outgoing request was never sent.
export function submissionStatus(state: string | null, reason: string | null, receipt: string | null) {
  if (state === "RESERVED" || state === "RELEASED") return "Not submitted";
  if (state === "UNKNOWN") return "Outcome unknown";
  if (state === "FAILED") {
    if (["load_gone", "load_not_open", "shipment_changed", "ceiling_below_rate", "not_sent"].includes(reason ?? "")) return "Not submitted";
    if (["invalid_rate", "unknown_load", "not_found"].includes(reason ?? "")) return "Rejected by TMS";
    return "Submission evidence unavailable";
  }
  return label(receipt);
}
