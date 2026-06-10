from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from app.api_client import backend
from app.charts import make_service_usage_chart

router = Router()


@router.message(Command("service"))
async def cmd_service(message: Message):
    try:
        services = await backend.get_services()
    except Exception:
        await message.answer("Не удалось получить список сервисов. Попробуй позже.")
        return

    if not services:
        await message.answer("Сервисов пока нет.")
        return

    lines = ["🏦 *Доступные сервисы:*\n"]
    for i, s in enumerate(services, 1):
        lines.append(f"{i}. {s['service_name']} _{s['service_type']}_")

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("service_usage"))
async def cmd_service_usage(message: Message):
    parts = message.text.split()[1:]  # drop command token

    if not parts:
        await message.answer(
            "Укажи название сервиса и опционально количество дней (1-14).\n"
            "Например:\n`/service_usage Переводы 7`",
            parse_mode="Markdown",
        )
        return

    # If last token is a number — treat it as days
    if parts[-1].isdigit():
        days = min(max(int(parts[-1]), 1), 14)
        service_name = " ".join(parts[:-1])
    else:
        days = 10
        service_name = " ".join(parts)

    if not service_name:
        await message.answer("Укажи название сервиса.")
        return

    try:
        data = await backend.get_service_usage(service_name, days)
    except Exception as e:
        err = str(e)
        if "404" in err:
            await message.answer(f"Сервис «{service_name}» не найден. Проверь `/service`.")
        else:
            await message.answer(f"Ошибка сервера: {e}")
        return

    if not data["data"]:
        await message.answer(f"Нет данных за последние {days} дней для *{data['service_name']}*.", parse_mode="Markdown")
        return

    chart_buf = make_service_usage_chart(data)

    total = sum(e["session_count"] for e in data["data"])
    caption = (
        f"📈 *{data['service_name']}*\n"
        f"Период: последние {len(data['data'])} дн.\n"
        f"Всего сессий: {total}\n"
        f"Медиана в день: {data['median_sessions']:.1f}"
    )

    await message.answer_photo(
        photo=BufferedInputFile(chart_buf.read(), filename="service_usage.png"),
        caption=caption,
        parse_mode="Markdown",
    )
