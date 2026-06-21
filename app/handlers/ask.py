import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.api_client import backend

router = Router()


def _extract_detail(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        try:
            return e.response.json().get("detail", str(e))
        except Exception:
            return e.response.text or str(e)
    return str(e)


@router.message(Command("ask"))
async def cmd_ask(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Задай вопрос после команды. Например:\n"
            "`/ask Сколько critical аномалий за последние 7 дней?`",
            parse_mode="Markdown",
        )
        return

    question = parts[1].strip()
    thinking = await message.answer("🤔 Анализирую запрос...")

    try:
        result = await backend.ask(question)
    except Exception as e:
        await thinking.delete()
        detail = _extract_detail(e)
        if "503" in str(e):
            await message.answer("YandexGPT не настроен на сервере (нет API-ключа).")
        else:
            await message.answer(f"Не удалось выполнить запрос:\n{detail}")
        return

    await thinking.delete()
    await message.answer(result["answer"])
