"""Selling: load search now; negotiation, reservation and close follow (section 9).

Load details reach the agent only through core.loads.public_view, and only once the
call's own row shows an eligible MC and a passed code (INV-2, INV-3).
"""

import asyncio
import uuid
from datetime import datetime
from typing import Protocol

from service.adapters.tms.client import TmsUnavailable
from service.adapters.twin import Data
from service.bookings import Bookings
from service.calls import CallRows, Decide, Reply, Unchanged, answer, is_verified, set_outcome
from service.core.loads import Search, public_view, search_terms, select_offers
from service.core.models import Load, LoadSummary
from service.core.money import parse_ask
from service.core.negotiation import Action, Step, respond
from service.core.pricing import PricingPolicy, Terms, price_load

SEARCH_LIMIT = 50  # TMS results considered before choosing at most three


class Board(Protocol):
    """The TMS reads that selling needs. TmsClient is the real one."""

    async def query(
        self,
        *,
        equipment: str | None = None,
        origin_state: str | None = None,
        dest_state: str | None = None,
        limit: int = 20,
    ) -> list[LoadSummary]: ...

    async def get(self, load_id: str) -> Load | None: ...


class Sales:
    def __init__(
        self,
        *,
        rows: CallRows,
        board: Board,
        bookings: Bookings,
        pricing: PricingPolicy,
        pricing_secret: bytes,
        blocked: frozenset[str],
    ) -> None:
        self.rows, self.board, self.bookings = rows, board, bookings
        self.pricing, self.pricing_secret, self.blocked = pricing, pricing_secret, blocked

    async def find_loads(
        self, run_id: str, equipment: str | None, origin_state: str | None, dest_state: str | None
    ) -> Reply:
        search = search_terms(equipment, origin_state, dest_state)
        if search is None:
            return await self.rows.step(run_id, "find_loads", answer("invalid_search"))
        if not is_verified(await self.rows.read(run_id)):  # before any load detail is fetched
            return await self.rows.step(run_id, "find_loads", answer("not_verified"))
        try:
            loads = await self._open_loads(search)
        except TmsUnavailable:
            failed = _searched(search, set_outcome("tms_unavailable"))
            return await self.rows.step(run_id, "find_loads", failed)
        priced = [(load, terms) for load in loads if (terms := self._terms(load))]

        def decide(data: Data, now: datetime) -> Reply:
            if not priced:  # a load we cannot price is never offered (D-11)
                status = "pricing_review_required" if loads else "no_match"
                if data["outcome"] != "negotiation_failed":
                    data["outcome"] = status
                return {"status": status}
            data["policy_version"] = self.pricing.version
            if data["outcome"] != "negotiation_failed":  # a failed negotiation stays failed
                data["outcome"] = None
            for load, terms in priced:  # a repeat keeps our offer, within today's terms (INV-1)
                kept = data["offers"].get(load.load_id, terms.opening)
                data["offers"][load.load_id] = min(max(kept, terms.opening), terms.cap)
            offered = {load.load_id: data["offers"][load.load_id] for load, _ in priced}
            return {"status": "found", "offers": offered}

        reply = await self.rows.step(run_id, "find_loads", _searched(search, decide))
        if reply["status"] != "found":
            return reply
        views = [public_view(load, reply["offers"][load.load_id]) for load, _ in priced]
        return {"status": "found", "loads": views}

    async def negotiate(self, run_id: str, load_id: str, ask: str) -> Reply:
        """Answer one counter-offer. On agreement, reserve the load; nothing is sent (D-22).

        The load is read again each time, so every number is checked against today's
        ceiling. Each answer is computed inside the call row's version-checked write, so
        concurrent requests cannot share a round. An acceptance is first claimed on the
        call row, which allows one per call; then the booking row decides who holds the
        load (D-24). A claim left by an earlier attempt is resolved first, through the
        booking row: settled if it reserved, otherwise voided there and dropped, so its
        first request can never reserve later and the counter is priced afresh.
        """
        data = await self.rows.read(run_id)
        early = _refusal(data, load_id)
        if early is not None:
            return await self.rows.step(run_id, "negotiate", answer(early["status"], early))
        claim = data["accepting"]
        if claim is not None:  # voided on the booking row, so its first request cannot reserve
            now = self.rows.now()
            held = await self.bookings.void(load_id, claim_id=claim["id"], call_id=run_id, now=now)
            if held is not None:
                return await self.rows.step(run_id, "negotiate", _settle(claim["id"], held))
            await self.rows.step(run_id, "negotiate", _abandon(claim["id"]))
        try:
            terms = await self._fresh_terms(load_id)
        except TmsUnavailable:
            return await self.rows.step(run_id, "negotiate", set_outcome("tms_unavailable"))
        if terms is None:
            return await self.rows.step(run_id, "negotiate", _drop(load_id))
        reply = await self.rows.step(run_id, "negotiate", _answer(load_id, ask, terms))
        if reply["status"] != "accepting":
            return reply
        held = await self.bookings.reserve(
            load_id,
            claim_id=reply["id"],
            call_id=run_id,
            mc=reply["mc"],
            rate=reply["rate"],
            cohort=self.rows.cohort,
            now=self.rows.now(),
        )
        return await self.rows.step(run_id, "negotiate", _settle(reply["id"], held))

    async def close(self, run_id: str, summary: str | None) -> Reply:
        """Record that the call ended. A repeat changes nothing, so the first close stands."""

        def decide(data: Data, now: datetime) -> Reply | Unchanged:
            if data["closed_at"] is not None:
                return Unchanged({"status": "closed"})
            data["closed_at"], data["summary"] = now.isoformat(), summary
            return {"status": "closed"}

        return await self.rows.step(run_id, "close", decide)

    async def _fresh_terms(self, load_id: str) -> Terms | None:
        """Today's terms for the load, or None if it is gone, blocked or cannot be priced."""
        load = await self.board.get(load_id)
        if load is None or not select_offers([load], self.rows.now(), self.blocked):
            return None
        return self._terms(load)

    async def _open_loads(self, search: Search) -> list[Load]:
        """Full details of up to three offerable loads on the lane, skipping held ones."""
        now = self.rows.now()
        found = await self.board.query(
            equipment=search["equipment"],
            origin_state=search["origin_state"],
            dest_state=search["dest_state"],
            limit=SEARCH_LIMIT,
        )
        excluded = self.blocked | await self.bookings.held(load.load_id for load in found)
        picked = select_offers(found, now, excluded, **search)
        reads = await asyncio.gather(*(self._read(load.load_id) for load in picked))
        if picked and all(isinstance(read, TmsUnavailable) for read in reads):
            raise TmsUnavailable("No load details could be read.")
        details = [read for read in reads if isinstance(read, Load)]
        return select_offers(details, self.rows.now(), excluded, **search)  # rechecked as read

    async def _read(self, load_id: str) -> Load | TmsUnavailable | None:
        """One load's details. One failed read skips that load rather than the search."""
        try:
            return await self.board.get(load_id)
        except TmsUnavailable as error:
            return error

    def _terms(self, load: Load) -> Terms | None:
        policy, secret = self.pricing, self.pricing_secret
        return price_load(load.load_id, load.loadboard_rate, load.max_rate, policy, secret)


def _searched(search: Search, decide: Decide) -> Decide:
    """Record what was asked, but only on a call that is still verified when it is written."""

    def guarded(data: Data, now: datetime) -> Reply | Unchanged:
        if not is_verified(data):
            return {"status": "not_verified"}
        data["search"] = dict(search)
        return decide(data, now)

    return guarded


def _refusal(data: Data, load_id: str) -> Reply | None:
    """Why this counter cannot be negotiated, from the call's own row."""
    agreement, claim = data["agreement"], data["accepting"]
    if not is_verified(data):
        return {"status": "not_verified"}
    if agreement is not None:
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


def _drop(load_id: str) -> Decide:
    """The load is gone, held by another call, or cannot be priced: stop offering it."""

    def decide(data: Data, now: datetime) -> Reply:
        data["offers"].pop(load_id, None)
        return {"status": "load_gone", "load_id": load_id}

    return decide


def _answer(load_id: str, ask: str, terms: Terms) -> Decide:
    """The counter's answer, from the row as it is at the moment of writing."""

    def decide(data: Data, now: datetime) -> Reply:
        refused = _refusal(data, load_id)
        if refused is not None:
            return refused
        if data["accepting"] is not None:  # another request on this load is accepting now
            return {"status": "busy"}
        amount = parse_ask(ask)
        offer = min(max(int(data["offers"][load_id]), terms.opening), terms.cap)  # INV-1
        last = data["last_counter"]
        if last and amount is not None and (last["load_id"], last["ask"]) == (load_id, amount):
            data["offers"][load_id] = offer  # the same ask uses no round (D-26), at today's bound
            return {**last["reply"], "offer": offer} if "offer" in last["reply"] else last["reply"]
        step = respond(terms, data["rounds"], offer, ask)
        data["rounds"] = step.rounds_used
        reply = _apply(data, load_id, step)
        if amount is not None and step.action is not Action.ACCEPT:
            data["last_counter"] = {"load_id": load_id, "ask": amount, "reply": reply}
        return reply

    return decide


def _apply(data: Data, load_id: str, step: Step) -> Reply:
    if step.action is Action.ACCEPT:
        claim = {"id": uuid.uuid4().hex, "load_id": load_id, "rate": step.rate, "mc": data["mc"]}
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


def _settle(claim_id: str, held: Data | None) -> Decide:
    """Finish one claim, by its ID: record the reservation as its booking row holds it, or
    drop a load that was lost. A late helper for an older claim changes nothing.
    """

    def decide(data: Data, now: datetime) -> Reply:
        claim = data["accepting"]
        if claim is None or claim["id"] != claim_id:
            return {"status": "superseded"}
        load_id, data["accepting"] = claim["load_id"], None
        if held is None:
            data["offers"].pop(load_id, None)
            return {"status": "load_gone", "load_id": load_id}
        data["agreement"] = {"load_id": load_id, "rate": held["rate"], "mc": held["mc"]}
        return {"status": "agreed", "load_id": load_id, "rate": held["rate"]}

    return decide


def _abandon(claim_id: str) -> Decide:
    """Drop a claim that never got its booking row, so nothing of it outlives today's terms."""

    def decide(data: Data, now: datetime) -> Reply:
        if data["accepting"] is not None and data["accepting"]["id"] == claim_id:
            data["accepting"] = None
        return {"status": "claim_dropped"}

    return decide
