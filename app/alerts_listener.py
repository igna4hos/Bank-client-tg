import asyncio
import logging

import httpx
from aiogram import Bot

from app.api_client import backend
from app.config import settings

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 100  # секунды
_MAX_ALERTS = 3

_SEVERITY_LABEL = {
    "low": "🟡 Low",
    "medium": "🟠 Medium",
    "high": "🔴 High",
    "critical": "🔴🔴 Critical",
}


def _format_alert(alert: dict) -> str:
    severity = _SEVERITY_LABEL.get(alert.get("severity", ""), alert.get("severity", ""))
    return (
        f"ID: `{alert['alert_id']}`\n"
        f"Время (МСК): {alert['detected_at_msk']}\n"
        f"Тип: {alert['anomaly_type']}\n"
        f"Метрика: {alert['metric_name']}\n"
        f"Критичность: {severity}\n"
        f"Детали: {alert['details']}"
    )


async def _broadcast(bot: Bot, alerts: list[dict]) -> None:
    try:
        users = await backend.get_all_users()
    except Exception as e:
        logger.error("Не удалось получить список пользователей: %s", e)
        return

    for user in users:
        for alert in alerts:
            try:
                await bot.send_message(user["chat_id"], _format_alert(alert), parse_mode="Markdown")
            except Exception as e:
                logger.warning("chat_id=%s: %s", user["chat_id"], e)


async def listen_for_alerts(bot: Bot) -> None:
    url = f"{settings.backend_url}/analytics/alerts/recent"
    last_count: int | None = None

    while True:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {"since_count": last_count or 0, "limit": _MAX_ALERTS}
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()

            current_count = data["total_count"]
            new_count = data["new_count"]

            if last_count is None:
                logger.info("Alerts listener: стартовый счётчик = %d", current_count)
                last_count = current_count
            elif new_count > 0:
                logger.info("Обнаружено %d новых аномалий, показываем %d", new_count, len(data["alerts"]))
                await _broadcast(bot, data["alerts"])
                last_count = current_count
            else:
                logger.debug("Новых аномалий нет, счётчик = %d", current_count)

        except Exception as e:
            logger.error("Ошибка при опросе аномалий: %s", e)

        await asyncio.sleep(_POLL_INTERVAL)
