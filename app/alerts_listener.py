import asyncio
import json
import logging

import httpx
from aiogram import Bot

from app.api_client import backend
from app.config import settings

logger = logging.getLogger(__name__)

_SEVERITY_LABEL = {
    "low": "🟡 Low",
    "medium": "🟠 Medium",
    "high": "🔴 High",
    "critical": "🔴🔴 Critical",
}


def _format_alert(alert: dict) -> str:
    severity = _SEVERITY_LABEL.get(alert.get("severity", ""), alert.get("severity", ""))
    return (
        f"⚠️ *Новая аномалия*\n\n"
        f"ID: `{alert['alert_id']}`\n"
        f"Тип: {alert['anomaly_type']}\n"
        f"Метрика: {alert['metric_name']}\n"
        f"Критичность: {severity}\n"
        f"Детали: {alert['details']}"
    )


async def _broadcast(bot: Bot, alert: dict) -> None:
    try:
        users = await backend.get_all_users()
    except Exception as e:
        logger.error("Не удалось получить список пользователей: %s", e)
        return

    text = _format_alert(alert)
    for user in users:
        try:
            await bot.send_message(user["chat_id"], text, parse_mode="Markdown")
        except Exception as e:
            logger.warning("Не удалось отправить сообщение пользователю %s: %s", user["chat_id"], e)


async def listen_for_alerts(bot: Bot) -> None:
    """Фоновая задача: подключается к SSE-потоку backend и рассылает аномалии всем пользователям."""
    url = f"{settings.backend_url}/analytics/alerts/stream"
    while True:
        try:
            logger.info("Подключаемся к SSE: %s", url)
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and len(line) > 6:
                            try:
                                alert = json.loads(line[6:])
                                await _broadcast(bot, alert)
                            except (json.JSONDecodeError, KeyError) as e:
                                logger.warning("Не удалось разобрать событие: %s | %s", line, e)
        except Exception as e:
            logger.error("SSE соединение прервано: %s. Переподключение через 10 сек.", e)
            await asyncio.sleep(10)
