from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.api_client import backend

router = Router()


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
        err = str(e)
        if "503" in err:
            await message.answer("YandexGPT не настроен на сервере (нет API-ключа).")
        elif "422" in err:
            await message.answer(f"Не удалось выполнить запрос: {e}")
        else:
            await message.answer(f"Ошибка: {e}")
        return

    await thinking.delete()
    await message.answer(result["answer"])
