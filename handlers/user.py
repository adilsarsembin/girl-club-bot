from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def send_welcome(message: types.Message):
    """
    Handler for the /start command. This is for all users.
    """
    await message.reply("Hi!\nWelcome to the GirlClub Bot! 💖")
