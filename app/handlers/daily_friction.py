from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from app.api_client import backend
from app.charts import make_friction_chart

router = Router()

_SEVERITY_EMOJI = {"low": "🟡", "medium": "🟠", "high": "🔴", "critical": "🔴🔴"}


def _fmt(val: float) -> str:
    return f"{val:.1f} сек"


def _build_caption(data: dict) -> str:
    lines = [
        f"📊 *{data['funnel_name']}*",
        f"Сервис: {data['service_name']}",
        f"📏 Benchmark: {data['benchmark_duration_sec']:.0f} сек\n",
    ]
    for s in data["stats"]:
        lines.append(f"*{s['date']}*")
        lines.append(f"• Мин:     {_fmt(s['min_duration_sec'])}")
        lines.append(f"• Среднее: {_fmt(s['avg_duration_sec'])}")
        lines.append(f"• Медиана: {_fmt(s['median_duration_sec'])}")
        lines.append(f"• Макс:    {_fmt(s['max_duration_sec'])}\n")
    return "\n".join(lines)


@router.message(Command("daily_friction"))
async def cmd_daily_friction(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Укажи название воронки. Например:\n`/daily_friction Перевод физлицу`",
            parse_mode="Markdown",
        )
        return

    funnel_name = parts[1].strip()

    try:
        data = await backend.get_daily_friction(funnel_name)
    except Exception as e:
        err = str(e)
        if "404" in err:
            await message.answer(f"Воронка «{funnel_name}» не найдена. Проверь `/funnel`.")
        else:
            await message.answer(f"Ошибка сервера: {e}")
        return

    if not data.get("stats"):
        await message.answer(f"Нет данных за последние 2 дня по воронке *{data['funnel_name']}*.", parse_mode="Markdown")
        return

    chart_buf = make_friction_chart(data)
    caption = _build_caption(data)

    await message.answer_photo(
        photo=BufferedInputFile(chart_buf.read(), filename="friction.png"),
        caption=caption,
        parse_mode="Markdown",
    )
