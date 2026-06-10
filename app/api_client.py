from typing import Optional

import httpx

from app.config import settings


class BackendClient:
    def __init__(self) -> None:
        self._base = settings.backend_url

    # ── Users ──────────────────────────────────────────────────────────────────

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

    async def get_all_users(self) -> list[dict]:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self._base}/users/", timeout=10.0)
            r.raise_for_status()
            return r.json()

    # ── Analytics ──────────────────────────────────────────────────────────────

    async def get_funnels(self) -> list[dict]:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self._base}/analytics/funnels", timeout=10.0)
            r.raise_for_status()
            return r.json()["funnels"]

    async def get_daily_friction(self, funnel_name: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{self._base}/analytics/daily-friction",
                params={"funnel_name": funnel_name},
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json()

    async def get_services(self) -> list[dict]:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self._base}/analytics/services", timeout=10.0)
            r.raise_for_status()
            return r.json()["services"]

    async def get_service_usage(self, service_name: str, days: int = 10) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{self._base}/analytics/service-usage",
                params={"service_name": service_name, "days": days},
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json()

    # ── Alerts ─────────────────────────────────────────────────────────────────

    async def assign_alert(self, alert_id: str, department: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self._base}/analytics/alerts/assign",
                json={"alert_id": alert_id, "department": department},
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json()


backend = BackendClient()
