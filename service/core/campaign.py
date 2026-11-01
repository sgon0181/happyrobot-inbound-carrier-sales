"""Append-only, load-specific permission for a controlled follow-up send."""


def intents(data):
    return [b for b in data["bookings"].values() if b.get("write_intent_id")]


def permission(data, call_id, load_id):
    spent = intents(data)
    if len(spent) >= 3:
        return None
    # The original authorized run allowed the initial send. Follow-ups require
    # a new recorded owner instruction, never a cohort or namespace reset.
    if not spent:
        return {"initial": True}
    baseline = sorted(b["write_intent_id"] for b in spent)
    for event in data["call_events"].values():
        if (
            event.get("action") == "live_booking_authorization"
            and event.get("load_id") == load_id
            and event.get("call_id") in (None, call_id)
            and event.get("baseline_intent_ids") == baseline
            and not event.get("consumed_intent_id")
        ):
            return event
    return None
