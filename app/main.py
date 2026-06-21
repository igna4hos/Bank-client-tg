import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.alerts_listener import listen_for_alerts
from app.config import settings
from app.handlers import anomaly, ask, do, help, start
from app.morning_report import morning_report_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(do.router)
    dp.include_router(anomaly.router)
    dp.include_router(ask.router)
    dp.include_router(help.router)

    asyncio.create_task(listen_for_alerts(bot))
    asyncio.create_task(morning_report_scheduler(bot))

    logging.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
