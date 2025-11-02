import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database.mysql import init_db as init_mysql_db
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from jobs import get_scheduler

load_dotenv()

async def main():
    """The main function to start the bot."""
    api_token = os.getenv("TELEGRAM_API_TOKEN")
    if not api_token:
        raise ValueError("TELEGRAM_API_TOKEN not found in environment variables")

    # Use proxy only if PROXY_URL is set (for production like PythonAnywhere)
    # For local testing, leave PROXY_URL empty or don't set it
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        session = AiohttpSession(proxy=proxy_url)
        print(f"Using proxy: {proxy_url}")
    else:
        session = AiohttpSession()
        print("Running without proxy (local mode)")

    bot = Bot(token=api_token, session=session)
    scheduler = get_scheduler()
    scheduler.start()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    init_mysql_db()
    dp.include_routers(admin_router, user_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
