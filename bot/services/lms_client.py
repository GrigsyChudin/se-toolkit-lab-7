"""HTTP client for the LMS backend API."""

from __future__ import annotations

import httpx

from config import settings


class LMSClient:
    def __init__(self) -> None:
        self._base = settings.lms_api_base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.lms_api_key}"}

    async def get_items(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self._base}/items/", headers=self._headers)
            r.raise_for_status()
            return r.json()

    async def get_pass_rates(self, lab: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{self._base}/analytics/pass-rates",
                headers=self._headers,
                params={"lab": lab},
            )
            r.raise_for_status()
            return r.json()
