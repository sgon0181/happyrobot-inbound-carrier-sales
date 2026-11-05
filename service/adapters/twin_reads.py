"""Coalesce fresh keyed reads at their scheduled SQL slot, without caching row state."""

import asyncio
import copy
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

MAX_KEYS = 128
MAX_WAITERS = 256


class TwinUnavailable(Exception):
    """Twin failed. A failed write may still have landed, so the next read decides."""


@dataclass
class _Batch[T]:
    table: str
    keys: set[str] = field(default_factory=set)
    waiters: list[tuple[tuple[str, ...], asyncio.Future[dict[str, T]]]] = field(
        default_factory=list
    )
    task: asyncio.Task[None] | None = None


class ReadBatches[T]:
    def __init__(
        self, read: Callable[[str, Callable[[], tuple[str, ...]]], Awaitable[dict[str, T]]]
    ) -> None:
        self._read = read
        self._open: dict[str, _Batch[T]] = {}
        self._tasks: set[asyncio.Task[None]] = set()
        self._waiting = 0
        self._closed = False

    async def get(self, table: str, keys: tuple[str, ...]) -> dict[str, T]:
        if self._closed or self._waiting >= MAX_WAITERS:
            raise TwinUnavailable("Twin read admission is unavailable.")
        batch = self._open.get(table)
        if batch is None or len(batch.keys | set(keys)) > MAX_KEYS:
            batch = _Batch(table)
            self._open[table] = batch
            batch.task = asyncio.create_task(self._dispatch(batch))
            self._tasks.add(batch.task)
            batch.task.add_done_callback(self._tasks.discard)
        future: asyncio.Future[dict[str, T]] = asyncio.get_running_loop().create_future()
        batch.keys.update(keys)
        batch.waiters.append((keys, future))
        self._waiting += 1
        try:
            return await future
        finally:
            self._waiting -= 1
            if all(waiter.done() for _, waiter in batch.waiters) and batch.task:
                self._detach(batch)
                batch.task.cancel()

    def _collect(self, batch: _Batch[T]) -> tuple[str, ...]:
        # Detach before dispatch. Later readers must obtain a later database snapshot.
        self._detach(batch)
        return tuple(
            dict.fromkeys(k for keys, waiter in batch.waiters if not waiter.done() for k in keys)
        )

    async def _dispatch(self, batch: _Batch[T]) -> None:
        try:
            rows = await self._read(batch.table, lambda: self._collect(batch))
        except TwinUnavailable as exc:
            _reject(batch, exc)
        except asyncio.CancelledError:
            for _, waiter in batch.waiters:
                waiter.cancel()
            raise
        else:
            _resolve(batch, rows)
        finally:
            self._detach(batch)

    def _detach(self, batch: _Batch[T]) -> None:
        if self._open.get(batch.table) is batch:
            del self._open[batch.table]

    async def close(self) -> None:
        self._closed = True
        pending = list(self._tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


def _reject[T](batch: _Batch[T], error: TwinUnavailable) -> None:
    for _, waiter in batch.waiters:
        if not waiter.done():
            waiter.set_exception(error)


def _resolve[T](batch: _Batch[T], rows: dict[str, T]) -> None:
    for keys, waiter in batch.waiters:
        if not waiter.done():
            waiter.set_result(copy.deepcopy({key: rows[key] for key in keys if key in rows}))
