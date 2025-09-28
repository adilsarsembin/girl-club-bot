import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database.mysql import init_db as init_mysql_db
from handlers.admin import router as admin_router
from handlers.user import router as user_router

load_dotenv()

async def main():
    """The main function to start the bot."""
    api_token = os.getenv("TELEGRAM_API_TOKEN")
    if not api_token:
        raise ValueError("API_TOKEN not found in environment variables")

    init_mysql_db()
    bot = Bot(token=api_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(admin_router, user_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
