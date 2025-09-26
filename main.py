import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the token from the environment variable
# It's a good practice to handle the case where the token is not set
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise ValueError("No TELEGRAM_API_TOKEN found in environment variables")

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Handler for the /start command
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` command
    """
    await message.reply("Hi!\nI'm GirlClub Bot! Let's get started.")

async def main():
    """The main function to start the bot."""
    # Start polling for updates from Telegram
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Set up logging to see what the bot is doing
    logging.basicConfig(level=logging.INFO)
    # Run the main function
    asyncio.run(main())
