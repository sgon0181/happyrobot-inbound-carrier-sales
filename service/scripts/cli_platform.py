"""CLI-only HTTP transport with concurrent address-family connection handling."""

import asyncio
import httpx
from service.adapters.twin.client import Platform, PlatformError


class CliPlatform(Platform):
    def request(self, path, body=None, method=None):
        async def run():
            headers = {
                "Authorization": "Bearer " + self.key,
                "Content-Type": "application/json",
                "x-organization-id": self.values.get(
                    "HAPPYROBOT_ORG_ID", "01a17a99-0856-7f88-b09f-4b787e20413c"
                ),
                "x-twin-environment": "production",
            }
            async with httpx.AsyncClient(base_url=self.base, headers=headers, timeout=8) as client:
                try:
                    response = await client.request(
                        method or ("POST" if body is not None else "GET"), path, json=body
                    )
                    if response.status_code >= 400:
                        try:
                            detail = response.json().get("message", "request rejected")
                        except (ValueError, AttributeError):
                            detail = "request rejected"
                        for value in self.values.values():
                            if isinstance(value, str) and len(value) > 8:
                                detail = detail.replace(value, "[REDACTED]")
                        raise PlatformError(response.status_code, detail)
                    return response.json()
                except (httpx.HTTPError, ValueError):
                    raise PlatformError("unavailable") from None

        return asyncio.run(run())
