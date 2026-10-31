"""Test helpers. Importing the tests blocks every connection except to this machine."""

import socket

from service.adapters.tms.client import TmsClient, TmsSettings

LOOPBACK = {"127.0.0.1", "::1"}


class NetworkBlocked(Exception):
    pass


def block_external_network():
    def guarded(original):
        def connect(self, address):
            if self.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in LOOPBACK:
                raise NetworkBlocked("Tests may only connect to this machine.")
            return original(self, address)

        return connect

    socket.socket.connect = guarded(socket.socket.connect)
    socket.socket.connect_ex = guarded(socket.socket.connect_ex)


def client_for(fake, **overrides):
    """A client with short timeouts, pointed at a local fake TMS."""
    values = dict(
        host="127.0.0.1", port=fake.port, token=fake.token, read_budget_seconds=1.5,
        attempt_seconds=0.25, write_seconds=0.25, booking_enabled=True,
    )
    values.update(overrides)
    return TmsClient(TmsSettings(**values))
