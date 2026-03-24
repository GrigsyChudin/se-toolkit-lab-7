"""HTTP client for the LMS backend API."""

from __future__ import annotations

import httpx

from config import settings


class LMSClient:
    def __init__(self) -> None:
        self._base = settings.lms_api_base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.lms_api_key}"}

    async def _get(self, path: str, **params) -> list | dict:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{self._base}{path}", headers=self._headers, params=params)
            r.raise_for_status()
            return r.json()

    async def _post(self, path: str, body: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{self._base}{path}", headers=self._headers, json=body or {})
            r.raise_for_status()
            return r.json()

    async def get_items(self) -> list[dict]:
        return await self._get("/items/")

    async def get_learners(self) -> list[dict]:
        return await self._get("/learners/")

    async def get_scores(self, lab: str) -> list[dict]:
        return await self._get("/analytics/scores", lab=lab)

    async def get_pass_rates(self, lab: str) -> list[dict]:
        return await self._get("/analytics/pass-rates", lab=lab)

    async def get_timeline(self, lab: str) -> list[dict]:
        return await self._get("/analytics/timeline", lab=lab)

    async def get_groups(self, lab: str) -> list[dict]:
        return await self._get("/analytics/groups", lab=lab)

    async def get_top_learners(self, lab: str, limit: int = 10) -> list[dict]:
        return await self._get("/analytics/top-learners", lab=lab, limit=limit)

    async def get_completion_rate(self, lab: str) -> dict:
        return await self._get("/analytics/completion-rate", lab=lab)

    async def trigger_sync(self) -> dict:
        return await self._post("/pipeline/sync")
