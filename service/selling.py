"""Selling: load search now; negotiation, reservation and close follow (section 9).

Load details reach the agent only through core.loads.public_view, and only once the
call's own row shows an eligible MC and a passed code (INV-2, INV-3).
"""

import asyncio
from collections.abc import Awaitable
from datetime import datetime
from typing import Protocol

from service.adapters.tms.client import TmsUnavailable
from service.adapters.twin import Data
from service.bookings import Bookings
from service.calls import CallRows, Decide, Reply, Unchanged, answer, is_verified, set_outcome
from service.core.loads import Search, public_view, reservation_view, search_terms, select_offers
from service.core.models import Load, LoadSummary
from service.core.money import parse_ask
from service.core.pricing import PricingPolicy, Terms, price_load
from service.sale_decisions import abandon, answer_counter, drop, refusal, settle

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
            return await self.rows.step(run_id, "find_loads", failed, {"search": dict(search)})
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
            views = [public_view(load, data["offers"][load.load_id]) for load, _ in priced]
            return {"status": "found", "loads": views}  # its event keeps what was pitched

        return await self.rows.step(
            run_id, "find_loads", _searched(search, decide), {"search": dict(search)}
        )

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
        heard = {"load_id": load_id, "ask": parse_ask(ask), "heard": ask}  # on every event

        def log(decide: Decide) -> Awaitable[Reply]:
            return self.rows.step(run_id, "negotiate", decide, heard)

        data = await self.rows.read(run_id)
        early = refusal(data, load_id)
        if early is not None:
            return await log(lambda current, now: refusal(current, load_id) or {"status": "busy"})
        claim = data["accepting"]
        if claim is not None:  # voided on the booking row, so its first request cannot reserve
            now = self.rows.now()
            held = await self.bookings.void(load_id, claim_id=claim["id"], call_id=run_id, now=now)
            if held is not None:
                return await log(settle(claim["id"], held))
            await log(abandon(claim["id"]))
        try:
            priced = await self._fresh_terms(load_id)
        except TmsUnavailable:
            return await log(set_outcome("tms_unavailable"))
        if priced is None:
            return await log(drop(load_id))
        load, terms = priced
        reply = await log(answer_counter(load_id, ask, terms))
        if reply["status"] != "accepting":
            return reply
        held = await self.bookings.reserve(
            load_id,
            claim_id=reply["id"],
            call_id=run_id,
            mc=reply["mc"],
            rate=reply["rate"],
            cohort=reply["cohort"],
            now=self.rows.now(),
            load=reservation_view(load),
        )
        return await log(settle(reply["id"], held))

    async def close(self, run_id: str, summary: str | None) -> Reply:
        """Record that the call ended. A repeat changes nothing, so the first close stands."""

        def decide(data: Data, now: datetime) -> Reply | Unchanged:
            if data["closed_at"] is not None:
                return Unchanged({"status": "closed"})
            data["closed_at"], data["summary"] = now.isoformat(), summary
            return {"status": "closed"}

        return await self.rows.step(run_id, "close", decide)

    async def _fresh_terms(self, load_id: str) -> tuple[Load, Terms] | None:
        """Today's terms for the load, or None if it is gone, blocked or cannot be priced."""
        load = await self.board.get(load_id)
        if load is None or not select_offers([load], self.rows.now(), self.blocked):
            return None
        terms = self._terms(load)
        return None if terms is None else (load, terms)

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
