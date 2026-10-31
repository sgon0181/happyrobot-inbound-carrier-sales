"""Which loads may be offered. Search also returns PENDING records, so nothing is assumed."""

MAX_OFFERS = 3


def is_offerable(load, now, blocked_ids=frozenset()):
    return (
        load.status == "OPEN"
        and load.pickup_datetime is not None
        and load.pickup_datetime > now
        and load.load_id not in blocked_ids
    )


def select_offers(loads, now, blocked_ids=frozenset(), equipment=None, origin_state=None,
                  dest_state=None):
    """Recheck the TMS's matches locally, then rank by pickup time."""

    def matches(load):
        return (
            (equipment is None or load.equipment_type == equipment)
            and (origin_state is None or load.origin.state == origin_state)
            and (dest_state is None or load.destination.state == dest_state)
        )

    offers = [load for load in loads if is_offerable(load, now, blocked_ids) and matches(load)]
    offers.sort(key=lambda load: load.pickup_datetime)
    return offers[:MAX_OFFERS]
