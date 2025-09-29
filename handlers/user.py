from aiogram import Bot, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommandScopeChat, Message

from database.anonymous import save_anon_message
from database.events import get_all_events
from database.quotes import get_random_quote
from database.users import add_user, get_all_user_ids_by_role
from filters import IsAdmin
from states.anonymous import AnonymousStates

router = Router()

user_commands = [
    types.BotCommand(command="start", description="Start bot"),
    types.BotCommand(command="quote", description="Get random quote"),
    types.BotCommand(command="anonymous_message", description="Send your anonymous message"),
    types.BotCommand(command="events", description="Get upcoming events"),
]
admin_commands = user_commands + [
    types.BotCommand(command="add_event", description="Add event"),
    types.BotCommand(command="add_quote", description="Add quote"),
    types.BotCommand(command="send_all", description="Send to all"),
    types.BotCommand(command="deactivate_event", description="Deactivate event")
]

@router.message(CommandStart())
async def send_welcome(message: types.Message, bot: Bot):
    """
    Handler for the /start command. This is for all users.
    """
    await message.reply("Hi!\nWelcome to the GirlClub Bot! 💖")
    admin_command = IsAdmin()
    is_admin = await admin_command(message)
    role = 'admin' if is_admin else 'user'
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name, role)
    if is_admin:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))


@router.message(Command("quote"))
async def get_quote(message: types.Message):
    quote = get_random_quote()
    await message.reply(f"💖 {quote}")


@router.message(Command("anonymous_message"))
async def cmd_anon(message: Message, state: FSMContext):
    await message.reply("Send your anonymous message:")
    await state.set_state(AnonymousStates.waiting_for_message)


@router.message(AnonymousStates.waiting_for_message)
async def process_anon(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    save_anon_message(message.from_user.id, text)
    formatted = f"You have anonymous message: {text}"
    admin_ids = get_all_user_ids_by_role('admin')
    for admin_id in admin_ids:
        await bot.send_message(admin_id, formatted)
    await message.reply("Message sent anonymously!")
    await state.clear()


@router.message(Command("events"))
async def get_events(message: Message):
    events = get_all_events()
    if not events:
        await message.reply("No events yet.")
        return
    for _, planned_at, place, theme in events:
        formatted = f"📅 {planned_at}\n📍 {place}\n🎯 {theme}"
        await message.reply(formatted)
