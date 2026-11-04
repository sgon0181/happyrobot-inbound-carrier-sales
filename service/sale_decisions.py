"""Call-row negotiation decisions, applied atomically by CallRows.step.

These functions change only the supplied row. Sales owns network reads and reservation.
"""

import uuid
from datetime import datetime

from service.adapters.twin import Data
from service.calls import Decide, Reply, is_verified
from service.core.loads import same_shipment
from service.core.models import Load
from service.core.money import parse_ask
from service.core.negotiation import Action, Step, respond
from service.core.pricing import Terms


def refusal(data: Data, load_id: str) -> Reply | None:
    """Why this counter cannot be negotiated, from the call's own row."""
    agreement, claim = data["agreement"], data["accepting"]
    if (data["closed_at"] or data.get("ended_at")) and claim is None:
        return {"status": "call_closed"}
    if not is_verified(data):
        return {"status": "not_verified"}
    if agreement is not None:
        if agreement["mc"] != data["mc"]:
            return {"status": "not_verified"}  # do not replay a legacy, mismatched agreement
        if agreement["load_id"] == load_id:  # a repeated accept finds its own reservation
            return {"status": "agreed", "load_id": load_id, "rate": agreement["rate"]}
        return {"status": "already_agreed"}  # one agreement per call (INV-6)
    if claim is not None and claim["load_id"] != load_id:
        return {"status": "already_agreed"}
    if data["outcome"] == "negotiation_failed":
        return {"status": "negotiation_failed"}
    if load_id not in data["offers"]:
        return {"status": "search_required"}
    return None


def drop(load_id: str) -> Decide:
    """The load is gone, held by another call, or cannot be priced: stop offering it."""

    def decide(data: Data, now: datetime) -> Reply:
        data["offers"].pop(load_id, None)
        return _unavailable(data, load_id)

    return decide


def answer_counter(load: Load, ask: str, terms: Terms, after_final: bool) -> Decide:
    """The counter's answer, from the row as it is at the moment of writing."""

    def decide(data: Data, now: datetime) -> Reply:
        load_id = load.load_id
        refused = refusal(data, load_id)
        if refused is not None:
            return refused
        if data["accepting"] is not None:  # another request on this load is accepting now
            return {"status": "busy"}
        if not same_shipment(load, data.get("shipments", {}).get(load_id)):
            data["offers"].pop(load_id)
            data["last_counter"] = None
            data.get("lowest_asks", {}).pop(load_id, None)
            return _unavailable(data, load_id) | {
                "message": "The shipment changed. Let me check the lane again."
            }
        return _price_ask(data, load_id, ask, terms, after_final)

    return decide


def _price_ask(data: Data, load_id: str, ask: str, terms: Terms, after_final: bool) -> Reply:
    amount = parse_ask(ask)
    offer = min(max(int(data["offers"][load_id]), terms.opening), terms.cap)  # INV-1
    last = data["last_counter"]
    if (
        after_final
        and last
        and last["load_id"] == load_id
        and last["reply"]["status"] == "final_offer"
    ) and ((amount is not None and amount > offer) or ask == "decline"):
        return _apply(data, load_id, Step(Action.FAILED, None, data["rounds"]))
    prior = data.setdefault("lowest_asks", {}).get(load_id)
    if amount is not None:
        data["lowest_asks"][load_id] = amount if prior is None else min(prior, amount)
    if last and amount is not None and (last["load_id"], last["ask"]) == (load_id, amount):
        data["offers"][load_id] = offer  # the same ask uses no round (D-26), at today's bound
        return {**last["reply"], "offer": offer} if "offer" in last["reply"] else last["reply"]
    step = respond(terms, data["rounds"], offer, ask)
    # A higher ask on unchanged freight cannot earn more than the carrier already requested.
    # A lower standing ask is not acceptance: quote it and wait for the carrier to agree.
    if prior is not None and step.rate is not None and step.rate > prior:
        action = Action.FINAL_OFFER if step.rounds_used == len(terms.targets) else Action.COUNTER
        step = Step(action, prior, step.rounds_used)
    data["rounds"] = step.rounds_used
    reply = _apply(data, load_id, step)
    if amount is not None and step.action is not Action.ACCEPT:
        data["last_counter"] = {"load_id": load_id, "ask": amount, "reply": reply}
    return reply


def _apply(data: Data, load_id: str, step: Step) -> Reply:
    if step.action is Action.ACCEPT:
        claim = {"id": uuid.uuid4().hex, "load_id": load_id, "rate": step.rate, "mc": data["mc"]}
        claim["cohort"] = data["cohort"]
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


def settle(claim_id: str, held: Data | None) -> Decide:
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
