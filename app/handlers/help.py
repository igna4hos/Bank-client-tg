from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

_HELP_TEXT = """
📖 *Доступные команды*

/do — открыть главное меню:
  1️⃣  Все доступные экраны
  2️⃣  Время на экране (график)
  3️⃣  Список сервисов
  4️⃣  Статистика использования сервиса (график)
  5️⃣  Бизнесы по отраслям (диаграммы)

/ask *<вопрос>* — задать аналитический вопрос на естественном языке
  Пример: `/ask Сколько аномалий за последние 7 дней?`

/anomaly\_assign *<alert\_id> <департамент>* — назначить аномалию на отдел
  Пример: `/anomaly_assign 3c180950-... DevOps`

/start — регистрация / приветствие

/help — это сообщение

---
🔔 Уведомления об аномалиях приходят автоматически.
📊 Утренний отчёт по аномалиям за прошлый день — в *08:00 МСК*.
""".strip()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(_HELP_TEXT, parse_mode="Markdown")
