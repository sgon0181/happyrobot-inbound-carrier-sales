"""Call-row negotiation decisions, applied atomically by CallRows.step.

These functions change only the supplied row. Sales owns network reads and reservation.
"""

import uuid
from datetime import datetime

from service.adapters.twin import Data
from service.calls import Decide, Reply, is_verified
from service.core.loads import same_shipment, shipment_terms
from service.core.models import Load
from service.core.money import parse_ask
from service.core.negotiation import Action, Step
from service.core.pricing import MAX_ROUNDS, Terms


def refusal(data: Data, load_id: str) -> Reply | None:
    """Why this counter cannot be negotiated, from the call's own row."""
    agreement, claim = data["agreement"], data["accepting"]
    if (data["closed_at"] or data.get("ended_at")) and claim is None:
        return {"status": "call_closed"}
    if not is_verified(data):
        return {"status": "not_verified"}
    if agreement is not None:
        return _existing_agreement(agreement, data["mc"], load_id)
    if claim is not None and claim["load_id"] != load_id:
        return {"status": "already_agreed"}
    if data["outcome"] == "negotiation_failed":
        return {"status": "negotiation_failed"}
    if load_id not in data["offers"]:
        return {"status": "search_required"}
    return None


def _existing_agreement(agreement: Data, mc: str, load_id: str) -> Reply:
    if agreement["mc"] != mc:
        return {"status": "not_verified"}
    if agreement["load_id"] == load_id:
        return {"status": "agreed", "load_id": load_id, "rate": agreement["rate"]}
    return {"status": "already_agreed"}


def drop(load_id: str) -> Decide:
    """The load is gone, held by another call, or cannot be priced: stop offering it."""

    def decide(data: Data, now: datetime) -> Reply:
        data["offers"].pop(load_id, None)
        return _unavailable(data, load_id)

    return decide


def remember_offer(data: Data, load: Load, terms: Terms) -> None:
    """Repeat a stable quote. Re-pitched material changes require fresh price consent."""
    load_id = load.load_id
    snapshots = data.setdefault("shipments", {})
    kept = data["offers"].get(load_id, terms.opening)
    if not same_shipment(load, snapshots.get(load_id)):
        kept = terms.opening
        data.get("lowest_asks", {}).pop(load_id, None)
        data.get("last_counters", {}).pop(load_id, None)
        data.get("counter_replies", {}).pop(load_id, None)
        if data["last_counter"] and data["last_counter"]["load_id"] == load_id:
            data["last_counter"] = None
    data["offers"][load_id] = min(kept, terms.cap)
    snapshots[load_id] = shipment_terms(load)


def answer_counter(load: Load, step: Step, mc: str, ask: str, cap: int) -> Decide:
    """The counter's answer, from the row as it is at the moment of writing."""

    def decide(data: Data, now: datetime) -> Reply:
        load_id = load.load_id
        if data["mc"] != mc:
            return {"status": "not_verified"}
        refused = refusal(data, load_id)
        if refused is not None:
            return refused
        if data["accepting"] is not None:  # another request on this load is accepting now
            return {"status": "busy"}
        if not same_shipment(load, data.get("shipments", {}).get(load_id)):
            data["offers"].pop(load_id)
            data["last_counter"] = None
            data.get("lowest_asks", {}).pop(load_id, None)
            data.get("last_counters", {}).pop(load_id, None)
            data.get("counter_replies", {}).pop(load_id, None)
            return _unavailable(data, load_id) | {
                "message": "The shipment changed. Let me check the lane again."
            }
        return _record_step(data, load_id, step, ask, cap)

    return decide


def _seen(data: Data, load_id: str) -> Data:
    seen: Data = data.setdefault("counter_replies", {}).setdefault(load_id, {})
    for event in data.get("events", []):
        if event.get("load_id") == load_id and event.get("status") in ("counter", "final_offer"):
            seen[str(event.get("ask"))] = True
    return seen


def _record_step(data: Data, load_id: str, step: Step, ask: str, cap: int) -> Reply:
    amount = parse_ask(ask)
    seen = _seen(data, load_id)
    current = min(data["offers"][load_id], cap)
    above_offer = amount is not None and amount > current
    countering = step.action in (Action.COUNTER, Action.FINAL_OFFER)
    spends = (above_offer or countering) and str(amount) not in seen
    if spends and data["rounds"] == MAX_ROUNDS:
        return _apply(data, load_id, Step(Action.FAILED, None, MAX_ROUNDS))
    if step.action in (Action.COUNTER, Action.FINAL_OFFER, Action.ACCEPT):
        rounds = max(data["rounds"] + int(spends), step.rounds_used)
        data["rounds"] = rounds
        if step.action is not Action.ACCEPT:
            action = Action.FINAL_OFFER if rounds == MAX_ROUNDS else Action.COUNTER
            step = Step(action, min(cap, step.rate or current), rounds)
        seen[str(amount)] = True
    return _apply(data, load_id, step)


def _apply(data: Data, load_id: str, step: Step) -> Reply:
    if step.action is Action.ACCEPT:
        claim = {"id": uuid.uuid4().hex, "load_id": load_id, "rate": step.rate, "mc": data["mc"]}
        claim["cohort"] = data["cohort"]
        claim["otp_route"] = data.get("otp_route")
        data["accepting"] = claim
        return {"status": "accepting", **data["accepting"]}
    if step.action is Action.FAILED:
        data["outcome"] = "negotiation_failed"
        return {"status": "negotiation_failed"}
    if step.action is Action.ASK_AGAIN:
        return {"status": "ask_again"}
    data["offers"][load_id] = step.rate
    final = step.action is Action.FINAL_OFFER
    return {
        "status": "final_offer" if final else "counter",
        "offer": step.rate,
        "round": step.rounds_used,
    }


def settle(claim_id: str, held: Data | None, *, terminal_recovery: bool = False) -> Decide:
    """Finish one claim, by its ID: record the reservation as its booking row holds it, or
    drop a load that was lost. A late helper for an older claim changes nothing.
    """

    def decide(data: Data, now: datetime) -> Reply:
        claim = data["accepting"]
        if claim is None or claim["id"] != claim_id:
            return {"status": "superseded"}
        if held is not None and (
            not is_verified(data) or data["mc"] != claim["mc"] or held["mc"] != claim["mc"]
        ):
            return {"status": "not_verified"}  # retain the claim; only a rep can free its booking
        load_id, data["accepting"] = claim["load_id"], None
        if held is None:
            data["offers"].pop(load_id, None)
            return _unavailable(data, load_id)
        data["agreement_needs_review"] = terminal_recovery or bool(
            data.get("closed_at") or data.get("ended_at")
        )
        data["agreement"] = {"load_id": load_id, "rate": held["rate"], "mc": held["mc"]}
        return {"status": "agreed", "load_id": load_id, "rate": held["rate"]}

    return decide


def abandon(claim_id: str) -> Decide:
    """Drop a claim that never got its booking row, so nothing of it outlives today's terms."""

    def decide(data: Data, now: datetime) -> Reply:
        if data["accepting"] is not None and data["accepting"]["id"] == claim_id:
            data["accepting"] = None
        return {"status": "claim_dropped"}

    return decide


def _unavailable(data: Data, load_id: str) -> Reply:
    """Give a truthful explanation and a next step without extra reads or stale alternatives."""
    if not is_verified(data):
        return {"status": "not_verified"}
    return {
        "status": "load_gone",
        "load_id": load_id,
        "message": "That load is no longer available. No reservation was made.",
        "next_action": "ask_to_search_again",
        "search": dict(data.get("search") or {}),
    }
