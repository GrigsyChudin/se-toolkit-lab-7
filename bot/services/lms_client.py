"""HTTP client for the LMS backend API."""

from __future__ import annotations

import httpx

from config import settings


class LMSClient:
    def __init__(self) -> None:
        self._base_url = settings.lms_api_base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.lms_api_key}"}

    async def get(self, path: str, **params: str) -> httpx.Response:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient() as client:
            return await client.get(url, headers=self._headers, params=params)
