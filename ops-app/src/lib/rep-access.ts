/** Only verified platform subjects explicitly assigned to the desk may mutate bookings. */
export function canManageBookings(subject: unknown, configured = process.env.OPS_REP_SUBJECTS): boolean {
  if (typeof subject !== "string" || !subject) return false;
  return (configured ?? "").split(",").some((id) => id.trim() === subject);
}
