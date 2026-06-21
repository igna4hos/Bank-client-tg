import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot

from app.api_client import backend

logger = logging.getLogger(__name__)

_MSK = timezone(timedelta(hours=3))
_SEVERITY_ORDER = ["critical", "high", "medium", "low"]
_SEVERITY_LABEL = {"low": "🟡 Low", "medium": "🟠 Medium", "high": "🔴 High", "critical": "🔴🔴 Critical"}


def _build_message(data: dict) -> str:
    yesterday = (datetime.now(_MSK) - timedelta(days=1)).strftime("%d.%m.%Y")
    lines = [f"📊 *Сводка аномалий за {yesterday}*\n", f"Всего: *{data['total']}*\n"]

    lines.append("*По типу:*")
    for item in data["by_type"]:
        lines.append(f"  • {item['anomaly_type']}: {item['count']}")

    lines.append("\n*По критичности:*")
    by_sev = {item["severity"]: item["count"] for item in data["by_severity"]}
    for sev in _SEVERITY_ORDER:
        if sev in by_sev:
            lines.append(f"  • {_SEVERITY_LABEL[sev]}: {by_sev[sev]}")

    return "\n".join(lines)


async def _send_report(bot: Bot) -> None:
    try:
        data = await backend.get_alerts_daily_summary()
        users = await backend.get_all_users()
    except Exception as e:
        logger.error("Не удалось получить данные для утреннего отчёта: %s", e)
        return

    text = "📊 *Утренний отчёт*\nАномалий за вчера не обнаружено. ✅" if data["total"] == 0 else _build_message(data)

    for user in users:
        try:
            await bot.send_message(user["chat_id"], text, parse_mode="Markdown")
        except Exception as e:
            logger.warning("chat_id=%s: %s", user["chat_id"], e)


async def morning_report_scheduler(bot: Bot) -> None:
    while True:
        now_msk = datetime.now(_MSK)
        target_msk = now_msk.replace(hour=8, minute=0, second=0, microsecond=0)
        if now_msk >= target_msk:
            target_msk += timedelta(days=1)

        wait_sec = (target_msk - now_msk).total_seconds()
        logger.info("Следующий утренний отчёт в %s МСК (через %.0f сек.)", target_msk.strftime("%H:%M"), wait_sec)
        await asyncio.sleep(wait_sec)

        logger.info("Отправляю утренний отчёт...")
        await _send_report(bot)
