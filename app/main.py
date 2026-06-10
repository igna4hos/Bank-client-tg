import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.alerts_listener import listen_for_alerts
from app.config import settings
from app.handlers import anomaly, daily_friction, funnel, service, start

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(funnel.router)
    dp.include_router(daily_friction.router)
    dp.include_router(service.router)
    dp.include_router(anomaly.router)

    asyncio.create_task(listen_for_alerts(bot))

    logging.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
