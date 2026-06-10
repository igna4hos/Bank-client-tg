from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.api_client import backend
from app.handlers.start import _get_nick

router = Router()

_SEVERITY_LABEL = {
    "low": "🟡 Low",
    "medium": "🟠 Medium",
    "high": "🔴 High",
    "critical": "🔴🔴 Critical",
}


def _alert_text(alert: dict, assigned_by: str) -> str:
    severity = _SEVERITY_LABEL.get(alert["severity"], alert["severity"])
    return (
        f"🚨 *Аномалия назначена на ваш отдел*\n\n"
        f"ID: `{alert['alert_id']}`\n"
        f"Тип: {alert['anomaly_type']}\n"
        f"Метрика: {alert['metric_name']}\n"
        f"Критичность: {severity}\n"
        f"Детали: {alert['details']}\n\n"
        f"Назначил: @{assigned_by}"
    )


@router.message(Command("anomaly_assign"))
async def cmd_anomaly_assign(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Формат: `/anomaly_assign <alert_id> <департамент>`\n"
            "Например:\n`/anomaly_assign 3c180950-55ef-4352-86a2-fe6639c8f256 DevOps`",
            parse_mode="Markdown",
        )
        return

    alert_id = parts[1].strip()
    department = parts[2].strip()
    assigned_by = _get_nick(message)

    try:
        result = await backend.assign_alert(alert_id, department)
    except Exception as e:
        err = str(e)
        if "404" in err:
            await message.answer("Аномалия с таким ID не найдена.")
        else:
            await message.answer(f"Ошибка: {e}")
        return

    users = result["users"]
    alert = result["alert"]

    if not users:
        await message.answer(f"В департаменте *{department}* нет зарегистрированных пользователей.", parse_mode="Markdown")
        return

    notification = _alert_text(alert, assigned_by)
    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user["chat_id"], notification, parse_mode="Markdown")
            sent += 1
        except Exception:
            pass

    await message.answer(
        f"✅ Аномалия `{alert_id}` назначена на *{department}*.\n"
        f"Уведомлено: {sent} из {len(users)} человек.",
        parse_mode="Markdown",
    )
