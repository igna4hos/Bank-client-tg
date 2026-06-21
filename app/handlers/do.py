from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from app.api_client import backend
from app.charts import make_friction_chart, make_industry_chart, make_service_usage_chart

router = Router()

_MENU = (
    "Выбери действие:\n\n"
    "1️⃣  Все доступные экраны\n"
    "2️⃣  Время на экранах\n"
    "3️⃣  Список сервисов\n"
    "4️⃣  Статистика использования сервиса\n"
    "5️⃣  Бизнесы по отраслям\n\n"
    "Введи цифру (1–5)"
)

_NUM_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=str(i)) for i in range(1, 6)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


class DoState(StatesGroup):
    choosing = State()
    waiting_screen = State()    # после выбора 2
    waiting_service = State()   # после выбора 4


# ── helpers ───────────────────────────────────────────────────────────────────

def _fmt(val: float) -> str:
    return f"{val:.1f} сек"


def _friction_caption(data: dict) -> str:
    lines = [
        f"📊 *{data['funnel_name']}*",
        f"Сервис: {data['service_name']}",
        f"📏 Benchmark: {data['benchmark_duration_sec']:.0f} сек\n",
    ]
    for s in data["stats"]:
        lines += [
            f"*{s['date']}*",
            f"• Мин:     {_fmt(s['min_duration_sec'])}",
            f"• Среднее: {_fmt(s['avg_duration_sec'])}",
            f"• Медиана: {_fmt(s['median_duration_sec'])}",
            f"• Макс:    {_fmt(s['max_duration_sec'])}\n",
        ]
    return "\n".join(lines)


async def _show_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(DoState.choosing)
    await message.answer(_MENU, reply_markup=_NUM_KEYBOARD)


# ── /do entry ─────────────────────────────────────────────────────────────────

@router.message(Command("do"))
async def cmd_do(message: Message, state: FSMContext):
    await _show_menu(message, state)


# ── choose action ─────────────────────────────────────────────────────────────

@router.message(DoState.choosing)
async def handle_choice(message: Message, state: FSMContext):
    choice = message.text.strip()

    if choice == "1":
        await _action_funnels(message, state)
    elif choice == "2":
        await message.answer(
            "Введи название экрана (допускаются опечатки):",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(DoState.waiting_screen)
    elif choice == "3":
        await _action_services(message, state)
    elif choice == "4":
        await message.answer(
            "Введи название сервиса и (опционально) количество дней через пробел.\n"
            "Пример: `Переводы 7`  или просто  `Переводы`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(DoState.waiting_service)
    elif choice == "5":
        await _action_industries(message, state)
    else:
        await message.answer("Введи цифру от 1 до 5.", reply_markup=_NUM_KEYBOARD)


# ── action 1: funnels ─────────────────────────────────────────────────────────

async def _action_funnels(message: Message, state: FSMContext):
    await state.clear()
    try:
        funnels = await backend.get_funnels()
    except Exception:
        await message.answer("Не удалось получить данные.", reply_markup=ReplyKeyboardRemove())
        return

    if not funnels:
        await message.answer("Экранов пока нет.")
        return

    lines = ["📋 *Все доступные экраны:*\n"]
    for i, f in enumerate(funnels, 1):
        lines.append(f"{i}. *{f['funnel_name']}*\n   └ {f['service_name']}")

    await message.answer("\n".join(lines), parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())


# ── action 2: screen timing (waiting_screen state) ───────────────────────────

@router.message(DoState.waiting_screen)
async def handle_screen_name(message: Message, state: FSMContext):
    await state.clear()
    funnel_name = message.text.strip()
    try:
        data = await backend.get_daily_friction(funnel_name)
    except Exception as e:
        err = str(e)
        if "404" in err:
            await message.answer(f"Экран «{funnel_name}» не найден. Посмотри список через /do → 1.")
        else:
            await message.answer(f"Ошибка: {e}")
        return

    if not data.get("stats"):
        await message.answer(f"Нет данных за последние 2 дня по *{data['funnel_name']}*.", parse_mode="Markdown")
        return

    chart_buf = make_friction_chart(data)
    await message.answer_photo(
        photo=BufferedInputFile(chart_buf.read(), filename="friction.png"),
        caption=_friction_caption(data),
        parse_mode="Markdown",
    )


# ── action 3: services ────────────────────────────────────────────────────────

async def _action_services(message: Message, state: FSMContext):
    await state.clear()
    try:
        services = await backend.get_services()
    except Exception:
        await message.answer("Не удалось получить список сервисов.", reply_markup=ReplyKeyboardRemove())
        return

    lines = ["🏦 *Доступные сервисы:*\n"]
    for i, s in enumerate(services, 1):
        lines.append(f"{i}. {s['service_name']} _{s['service_type']}_")

    await message.answer("\n".join(lines), parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())


# ── action 4: service usage (waiting_service state) ──────────────────────────

@router.message(DoState.waiting_service)
async def handle_service_input(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.strip().split()

    if parts and parts[-1].isdigit():
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
            await message.answer(f"Сервис «{service_name}» не найден. Посмотри список через /do → 3.")
        else:
            await message.answer(f"Ошибка: {e}")
        return

    if not data["data"]:
        await message.answer(f"Нет данных за {days} дней для *{data['service_name']}*.", parse_mode="Markdown")
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


# ── action 5: industries ──────────────────────────────────────────────────────

async def _action_industries(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⏳ Строю диаграммы...", reply_markup=ReplyKeyboardRemove())
    try:
        data = await backend.get_businesses_by_industry()
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        return

    if not data["industry_counts"]:
        await message.answer("Нет данных по отраслям.")
        return

    chart_buf = make_industry_chart(data)
    total_biz = sum(d["count"] for d in data["industry_counts"])
    await message.answer_photo(
        photo=BufferedInputFile(chart_buf.read(), filename="industries.png"),
        caption=f"🏭 *Бизнесы по отраслям*\nВсего компаний: {total_biz}",
        parse_mode="Markdown",
    )
