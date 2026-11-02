"""Selling: load search now; negotiation, reservation and close follow (section 9).

Load details reach the agent only through core.loads.public_view, and only once the
call's own row shows an eligible MC and a passed code (INV-2, INV-3).
"""

import asyncio
from datetime import datetime
from typing import Protocol

from service.adapters.tms.client import TmsUnavailable
from service.adapters.twin import Data
from service.bookings import Bookings
from service.calls import CallRows, Reply, answer, is_verified, set_outcome
from service.core.loads import Search, is_offerable, public_view, search_terms, select_offers
from service.core.models import Load, LoadSummary
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
            return await self.rows.step(run_id, "find_loads", set_outcome("tms_unavailable"))
        priced = [(load, terms) for load in loads if (terms := self._terms(load))]

        def decide(data: Data, now: datetime) -> Reply:
            if not is_verified(data):
                return {"status": "not_verified"}
            data["search"] = dict(search)
            if not priced:  # a load we cannot price is never offered (D-11)
                data["outcome"] = "pricing_review_required" if loads else "no_match"
                return {"status": data["outcome"]}
            data["outcome"], data["policy_version"] = None, self.pricing.version
            for load, terms in priced:
                data["offers"].setdefault(load.load_id, terms.opening)  # a repeat keeps our offer
            offered = {load.load_id: data["offers"][load.load_id] for load, _ in priced}
            return {"status": "found", "offers": offered}

        reply = await self.rows.step(run_id, "find_loads", decide)
        if reply["status"] != "found":
            return reply
        views = [public_view(load, reply["offers"][load.load_id]) for load, _ in priced]
        return {"status": "found", "loads": views}

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
        return [
            read for read in reads if isinstance(read, Load) and is_offerable(read, now, excluded)
        ]

    async def _read(self, load_id: str) -> Load | TmsUnavailable | None:
        """One load's details. One failed read skips that load rather than the search."""
        try:
            return await self.board.get(load_id)
        except TmsUnavailable as error:
            return error

    def _terms(self, load: Load) -> Terms | None:
        policy, secret = self.pricing, self.pricing_secret
        return price_load(load.load_id, load.loadboard_rate, load.max_rate, policy, secret)
