import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database.mysql import init_db as init_mysql_db
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from jobs import get_scheduler
from logging_config import setup_logging_from_env

load_dotenv()

logger = setup_logging_from_env()


async def main():
    api_token = os.getenv("TELEGRAM_API_TOKEN")
    if not api_token:
        logger.error("TELEGRAM_API_TOKEN not found in environment variables")
        raise ValueError("TELEGRAM_API_TOKEN not found in environment variables")

    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        session = AiohttpSession(proxy=proxy_url)
        logger.info(f"Using proxy: {proxy_url}")
    else:
        session = AiohttpSession()
        logger.info("Running without proxy (local mode)")

    bot = Bot(token=api_token, session=session)
    logger.info("Bot instance created successfully")

    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logger.info("Dispatcher created with memory storage")

    try:
        init_mysql_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    dp.include_routers(admin_router, user_router)
    logger.info("Routers registered successfully")

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during polling: {e}")
        raise
    finally:
        logger.info("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())
