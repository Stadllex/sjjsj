import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from database import init_db
from handlers import setup, game, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🎮 Начать новую игру"),
        BotCommand(command="admin", description="⚙️ Управление категориями"),
        BotCommand(command="commands", description="📋 Список всех команд"),
        BotCommand(command="cancel", description="❌ Отменить текущее действие"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не установлен!")

    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных готова.")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(setup.router)
    dp.include_router(game.router)
    dp.include_router(admin.router)

    await set_bot_commands(bot)

    logger.info("Бот запущен...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
