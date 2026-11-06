"""Durable carrier/load negotiation budget, shared by calls and service processes.

Reserve a decision before recording it on a call. If that second write fails,
the shared concession remains spent. No cross-row transaction is assumed.
"""

from collections.abc import Callable
from datetime import datetime

from service.adapters.twin import Data, Twin
from service.core.loads import same_shipment, shipment_terms
from service.core.models import Load
from service.core.money import parse_ask
from service.core.negotiation import Action, Step, respond
from service.core.pricing import MAX_ROUNDS, Terms


def key(mc: str, load_id: str) -> str:
    return f"{mc}:{load_id}"


async def quotes(twin: Twin, mc: str, priced: list[tuple[Load, Terms]]) -> dict[str, int]:
    rows = await twin.get_many("negotiations", [key(mc, load.load_id) for load, _ in priced])
    found = {}
    for load, terms in priced:
        row = rows.get(key(mc, load.load_id))
        if row and same_shipment(load, row.data["shipment"]):
            offer = row.data["offer"]
            if offer > terms.cap:
                offer = await twin.change(
                    "negotiations", key(mc, load.load_id), _retract(load, terms.cap)
                )
            if offer is not None:
                found[load.load_id] = offer
    return found


def _retract(load: Load, cap: int) -> Callable[[Data | None], tuple[Data | None, int | None]]:
    def edit(data: Data | None) -> tuple[Data | None, int | None]:
        if data is None or not same_shipment(load, data["shipment"]):
            return None, None
        data["offer"] = min(data["offer"], cap)
        return data, data["offer"]

    return edit


async def decide(
    twin: Twin,
    mc: str,
    run_id: str,
    load: Load,
    terms: Terms,
    call: Data,
    ask: str,
    after_final: bool,
    now: datetime,
) -> Step:
    """CAS serializes all callers of the same verified carrier and shipment."""

    def edit(previous: Data | None) -> tuple[Data | None, Step]:
        data = previous
        if data is None or not same_shipment(load, data["shipment"]):
            data = {
                "shipment": shipment_terms(load),
                "offer": terms.opening if previous else call["offers"][load.load_id],
                "rounds": 0,
                "best_ask": None,
                "seen": [],
                "events": [],
            }
        data["offer"] = min(data["offer"], terms.cap)
        data["rounds"] = max(data["rounds"], call["rounds"])
        step = _answer(data, terms, ask, after_final)
        amount = parse_ask(ask)
        if step.rounds_used > data["rounds"] and amount is not None:
            data["seen"].append(amount)
            data["best_ask"] = min(data["best_ask"] or amount, amount)
            data["events"].append(
                {
                    "run_id": run_id,
                    "at": now.isoformat(),
                    "ask": amount,
                    "offer": step.rate,
                    "round": step.rounds_used,
                }
            )
        data["rounds"] = step.rounds_used
        if step.action in (Action.COUNTER, Action.FINAL_OFFER, Action.ACCEPT):
            data["offer"] = step.rate
        if _opening_acceptance(previous, call, terms, step):
            return None, step
        return data, step

    return await twin.change("negotiations", key(mc, load.load_id), edit)


def _opening_acceptance(previous: Data | None, call: Data, terms: Terms, step: Step) -> bool:
    """A fresh absent-row read plus opening acceptance spends no shared concession.

    This decision linearizes at that fresh read. A later concurrent decision remains
    intact. Existing rows, lower accepts, repriced quotes and nonzero rounds still
    persist through CAS. Booking ownership remains a separate CAS.
    """
    return (
        previous is None
        and call["rounds"] == 0
        and call["offers"][terms.load_id] == terms.opening
        and step.action is Action.ACCEPT
        and step.rate == terms.opening
    )


def _answer(data: Data, terms: Terms, ask: str, after_final: bool) -> Step:
    amount, rounds, offer = parse_ask(ask), data["rounds"], data["offer"]
    if after_final and rounds == MAX_ROUNDS and ask == "decline":
        return Step(Action.FAILED, None, rounds)
    # Exact replay does not spend another turn, including across new calls.
    # Explicit refusal after the final quote takes precedence over replay.
    if amount in data["seen"] and amount is not None and amount > offer:
        if after_final and rounds == MAX_ROUNDS:
            return Step(Action.FAILED, None, rounds)
        action = Action.FINAL_OFFER if rounds == MAX_ROUNDS else Action.COUNTER
        return Step(action, offer, rounds)
    return respond(terms, rounds, offer, ask, data["best_ask"])
