from typing import Optional

import httpx

from app.config import settings


class BackendClient:
    def __init__(self) -> None:
        self._base = settings.backend_url

    async def get_user(self, telegram_nick: str) -> dict | None:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self._base}/users/{telegram_nick}", timeout=10.0)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()

    async def create_user(self, telegram_nick: str, chat_id: int, department: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self._base}/users/",
                json={"telegram_nick": telegram_nick, "chat_id": chat_id, "department": department},
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json()

    async def get_funnels(self) -> list[str]:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self._base}/analytics/funnels", timeout=10.0)
            r.raise_for_status()
            return r.json()["funnels"]

    async def get_daily_friction(self, funnel_id: Optional[str] = None) -> dict:
        async with httpx.AsyncClient() as c:
            params = {"funnel_id": funnel_id} if funnel_id else {}
            r = await c.get(
                f"{self._base}/analytics/daily-friction", params=params, timeout=30.0
            )
            r.raise_for_status()
            return r.json()


backend = BackendClient()
