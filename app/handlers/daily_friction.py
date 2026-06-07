from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.api_client import backend

router = Router()

_MAX_MSG = 4000


def _fmt(val: float) -> str:
    return f"{val:.1f} сек"


@router.message(Command("daily_friction"))
async def cmd_daily_friction(message: Message):
    parts = message.text.split(maxsplit=1)
    funnel_id = parts[1].strip() if len(parts) > 1 else None

    try:
        data = await backend.get_daily_friction(funnel_id)
    except Exception as e:
        await message.answer(f"Ошибка при получении данных: {e}")
        return

    stats = data["stats"]
    report_date = data["date"]

    if not stats:
        target = f"воронки `{funnel_id}`" if funnel_id else "всех воронок"
        await message.answer(f"Нет данных за *{report_date}* по {target}.", parse_mode="Markdown")
        return

    header = f"📊 *Статистика времени выполнения задач за {report_date}*\n\n"
    blocks = []
    for s in stats:
        blocks.append(
            f"🔹 *Воронка:* `{s['funnel_id']}`\n"
            f"• Мин:     {_fmt(s['min_duration_sec'])}\n"
            f"• Среднее: {_fmt(s['avg_duration_sec'])}\n"
            f"• Медиана: {_fmt(s['median_duration_sec'])}\n"
            f"• Макс:    {_fmt(s['max_duration_sec'])}\n"
        )

    # Split into chunks if message exceeds Telegram limit
    current = header
    for block in blocks:
        if len(current) + len(block) > _MAX_MSG:
            await message.answer(current, parse_mode="Markdown")
            current = block
        else:
            current += block

    await message.answer(current, parse_mode="Markdown")
