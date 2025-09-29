import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from urllib.parse import quote

from database.mysql import init_db as init_mysql_db
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from jobs import get_scheduler

load_dotenv()

async def main():
    """The main function to start the bot."""
    api_token = os.getenv("TELEGRAM_API_TOKEN")
    if not api_token:
        raise ValueError("API_TOKEN not found in environment variables")

    init_mysql_db()
    pa_username = os.getenv('PA_USERNAME')
    pa_password = os.getenv('PA_PASSWORD')
    proxy_url = f"http://{quote(pa_username)}:{quote(pa_password)}@proxy.server:3128"
    session = AiohttpSession(proxy=proxy_url)
    bot = Bot(token=api_token, session=session)
    scheduler = get_scheduler()
    scheduler.start()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(admin_router, user_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
