from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.api_client import backend

router = Router()


@router.message(Command("funnel"))
async def cmd_funnel(message: Message):
    try:
        funnels = await backend.get_funnels()
    except Exception:
        await message.answer("Не удалось получить данные. Попробуй позже.")
        return

    if not funnels:
        await message.answer("Воронок пока нет.")
        return

    lines = ["📋 *Список воронок:*\n"]
    for i, f in enumerate(funnels, 1):
        lines.append(f"{i}\\. *{f['funnel_name']}*\n   └ {f['service_name']}")

    await message.answer("\n".join(lines), parse_mode="MarkdownV2")
