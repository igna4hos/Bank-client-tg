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
        await message.answer("Не удалось получить данные от сервера. Попробуй позже.")
        return

    if not funnels:
        await message.answer("Данных по воронкам пока нет.")
        return

    lines = [f"{i + 1}\\. `{f}`" for i, f in enumerate(funnels)]
    await message.answer(
        "📋 *Список воронок:*\n\n" + "\n".join(lines),
        parse_mode="MarkdownV2",
    )
