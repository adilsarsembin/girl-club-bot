from aiogram import Bot, Router, types
from aiogram.filters import CommandStart
from aiogram.types import BotCommandScopeChat

from filters import IsAdmin

router = Router()

user_commands = [types.BotCommand(command="start", description="Start bot")]
admin_commands = user_commands + [
    types.BotCommand(command="admin", description="Admin panel"),
    types.BotCommand(command="add_event", description="Add event")
]

@router.message(CommandStart())
async def send_welcome(message: types.Message, bot: Bot):
    """
    Handler for the /start command. This is for all users.
    """
    await message.reply("Hi!\nWelcome to the GirlClub Bot! 💖")
    admin_command = IsAdmin()
    if await admin_command(message):
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
