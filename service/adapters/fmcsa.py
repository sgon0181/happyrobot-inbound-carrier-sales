"""FMCSA QCMobile docket lookup. The request URL carries the webKey, so it is never raised.

FMCSA answers from Fly.io but refuses this local machine with HTTP 403, which counts as
unavailable, never as an inactive or unknown carrier (docs/test-carriers.md).
"""

from dataclasses import dataclass, field
from typing import Any

import httpx

URL = "https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{mc}/"
MAX_BYTES = 2 * 1024 * 1024


class FmcsaUnavailable(Exception):
    """FMCSA gave no usable answer. Report it honestly; never treat it as a result."""


@dataclass(frozen=True, kw_only=True)
class FmcsaSettings:
    api_key: str = field(repr=False)
    url: str = URL
    timeout_seconds: float = 5.0


class Fmcsa:
    def __init__(
        self, settings: FmcsaSettings, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.settings = settings
        headers = {"Accept": "application/json"}
        self._http = httpx.AsyncClient(
            transport=transport, headers=headers, timeout=settings.timeout_seconds
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def carriers(self, mc: str) -> list[dict[str, Any]]:
        """The carrier records for a normalized MC, or an empty list if FMCSA has none."""
        if not mc.isdigit():
            raise ValueError("Normalize the MC before looking it up.")
        url = self.settings.url.format(mc=mc)
        try:
            response = await self._http.get(url, params={"webKey": self.settings.api_key})
        except httpx.HTTPError:
            raise FmcsaUnavailable("FMCSA did not answer.") from None
        if response.status_code == 404:
            return []
        if response.status_code != 200 or len(response.content) > MAX_BYTES:
            raise FmcsaUnavailable(f"FMCSA returned HTTP {response.status_code}.")
        try:
            payload = response.json()
        except ValueError:
            raise FmcsaUnavailable("FMCSA returned an unreadable reply.") from None
        return _carriers(payload)


def _carriers(payload: object) -> list[dict[str, Any]]:
    """The 'carrier' object of each content item. An application error is unavailable."""
    if not isinstance(payload, dict) or "content" not in payload or _is_error(payload):
        raise FmcsaUnavailable("FMCSA returned an error.")
    content = payload["content"]
    if content in (None, []):
        return []
    items = [content] if isinstance(content, dict) else content
    if not isinstance(items, list) or not all(_is_carrier_item(item) for item in items):
        raise FmcsaUnavailable("FMCSA returned an unexpected shape.")
    return [item["carrier"] for item in items]


def _is_error(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in ("error", "errorMessage", "exception"))


def _is_carrier_item(item: object) -> bool:
    return isinstance(item, dict) and isinstance(item.get("carrier"), dict)
