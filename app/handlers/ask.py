import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.api_client import backend
from app.yandex_gpt import fix_sql, generate_answer, generate_sql

router = Router()

_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)


async def _execute_sql(sql: str) -> dict:
    return await backend.execute_query(sql)


@router.message(Command("ask"))
async def cmd_ask(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Задай вопрос после команды. Например:\n"
            "`/ask Сколько аномалий critical за последние 7 дней?`",
            parse_mode="Markdown",
        )
        return

    question = parts[1].strip()
    thinking = await message.answer("🤔 Анализирую запрос...")

    # Step 1 — генерация SQL
    try:
        sql = generate_sql.__wrapped__(question) if hasattr(generate_sql, "__wrapped__") else await generate_sql(question)
    except Exception as e:
        await thinking.delete()
        await message.answer(f"Ошибка при обращении к YandexGPT: {e}")
        return

    # Убираем возможные markdown-блоки которые иногда добавляет LLM
    sql = re.sub(r"^```\w*\n?", "", sql).rstrip("`").strip()

    if not _SELECT_RE.match(sql):
        await thinking.delete()
        await message.answer(
            f"⚠️ Модель сгенерировала не SELECT-запрос. Попробуй переформулировать вопрос.\n\n`{sql}`",
            parse_mode="Markdown",
        )
        return

    # Step 2 — выполнение SQL (с одной попыткой авторемонта)
    result = None
    for attempt in range(2):
        try:
            result = await _execute_sql(sql)
            break
        except Exception as e:
            if attempt == 0:
                await thinking.edit_text("🔧 Исправляю запрос...")
                try:
                    sql = await fix_sql(question, sql, str(e))
                    sql = re.sub(r"^```\w*\n?", "", sql).rstrip("`").strip()
                except Exception:
                    pass
            else:
                await thinking.delete()
                await message.answer(
                    f"❌ Не удалось выполнить запрос даже после исправления.\n\nSQL:\n`{sql}`",
                    parse_mode="Markdown",
                )
                return

    if not result["rows"]:
        await thinking.delete()
        await message.answer(
            f"📭 Запрос выполнен, но данных не найдено.\n\nSQL:\n`{sql}`",
            parse_mode="Markdown",
        )
        return

    # Step 3 — интерпретация результатов
    await thinking.edit_text("💬 Формирую ответ...")
    try:
        answer = await generate_answer(question, sql, result["columns"], result["rows"])
    except Exception as e:
        await thinking.delete()
        await message.answer(f"Данные получены, но не удалось сформировать ответ: {e}")
        return

    await thinking.delete()
    await message.answer(answer)
