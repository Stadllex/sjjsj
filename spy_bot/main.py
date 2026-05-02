import asyncio
import logging
import os
import sys

# Ensure the bot's own directory is on the path regardless of where it's launched from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db
from handlers import setup, game, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is not set!")

    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database ready.")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers (order matters — more specific first)
    dp.include_router(setup.router)
    dp.include_router(game.router)
    dp.include_router(admin.router)

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
