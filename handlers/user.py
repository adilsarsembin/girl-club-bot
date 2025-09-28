from aiogram import Bot, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import BotCommandScopeChat

from database.quotes import get_random_quote
from database.users import add_user
from filters import IsAdmin

router = Router()

user_commands = [
    types.BotCommand(command="start", description="Start bot"),
    types.BotCommand(command="quote", description="Get random quote")
]
admin_commands = user_commands + [
    types.BotCommand(command="add_event", description="Add event"),
    types.BotCommand(command="add_quote", description="Add quote"),
    types.BotCommand(command="send_all", description="Send to all")
]

@router.message(CommandStart())
async def send_welcome(message: types.Message, bot: Bot):
    """
    Handler for the /start command. This is for all users.
    """
    await message.reply("Hi!\nWelcome to the GirlClub Bot! 💖")
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    admin_command = IsAdmin()
    if await admin_command(message):
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))


@router.message(Command("quote"))
async def get_quote(message: types.Message):
    quote = get_random_quote()
    await message.reply(f"💖 {quote}")
