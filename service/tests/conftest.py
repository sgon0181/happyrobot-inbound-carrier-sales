"""Every test may connect only to this machine, so no test can reach the real TMS or Twin."""

import socket
from collections.abc import Callable
from typing import Any

import pytest

LOOPBACK = {"127.0.0.1", "::1"}


class NetworkBlocked(Exception):
    """Not an OSError, so no retry loop can quietly swallow it."""


def _guard(original: Callable[[socket.socket, Any], Any]) -> Callable[[socket.socket, Any], Any]:
    def connect(self: socket.socket, address: Any) -> Any:
        if self.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in LOOPBACK:
            raise NetworkBlocked("Tests may only connect to this machine.")
        return original(self, address)

    return connect


@pytest.fixture(autouse=True)
def _no_external_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", _guard(socket.socket.connect))
    monkeypatch.setattr(socket.socket, "connect_ex", _guard(socket.socket.connect_ex))
