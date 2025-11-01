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
    types.BotCommand(command="start", description="Запустить бота"),
    types.BotCommand(command="help", description="Показать доступные команды"),
    types.BotCommand(command="quote", description="Получить случайную цитату"),
    types.BotCommand(command="anonymous_message", description="Отправить анонимное сообщение"),
    types.BotCommand(command="events", description="Посмотреть предстоящие события"),
]
admin_commands = user_commands + [
    types.BotCommand(command="add_event", description="Добавить событие"),
    types.BotCommand(command="add_quote", description="Добавить цитату"),
    types.BotCommand(command="send_all", description="Отправить всем"),
    types.BotCommand(command="deactivate_event", description="Деактивировать событие")
]

@router.message(CommandStart())
async def send_welcome(message: types.Message, bot: Bot):
    """
    Handler for the /start command. This is for all users.
    """
    await message.reply("Привет!\nДобро пожаловать в GirlClub Bot! 💖")
    admin_command = IsAdmin()
    is_admin = await admin_command(message)
    role = 'admin' if is_admin else 'user'
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name, role)
    if is_admin:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))


@router.message(Command("help"))
async def send_help(message: types.Message, bot: Bot):
    """
    Handler for the /help command. Shows available commands based on user role.
    """
    admin_command = IsAdmin()
    is_admin = await admin_command(message)

    help_text = "🤖 <b>GirlClub Bot - Доступные команды:</b>\n\n"

    if is_admin:
        help_text += "👤 <b>Пользовательские команды:</b>\n"
        for cmd in user_commands:
            if cmd.command != "help":  # Skip help command in list
                help_text += f"/{cmd.command} - {cmd.description}\n"

        help_text += "\n👑 <b>Администраторские команды:</b>\n"
        for cmd in admin_commands[len(user_commands):]:  # Get only admin-specific commands
            help_text += f"/{cmd.command} - {cmd.description}\n"

        help_text += "\n💡 <i>Используйте команды для управления клубом!</i>"
    else:
        help_text += "👤 <b>Доступные команды:</b>\n"
        for cmd in user_commands:
            help_text += f"/{cmd.command} - {cmd.description}\n"

        help_text += "\n💡 <i>Наслаждайтесь использованием бота!</i>"

    await message.reply(help_text, parse_mode="HTML")


@router.message(Command("quote"))
async def get_quote(message: types.Message):
    quote = get_random_quote()
    await message.reply(f"💖 {quote}")


@router.message(Command("anonymous_message"))
async def cmd_anon(message: Message, state: FSMContext):
    await message.reply("Отправьте ваше анонимное сообщение:")
    await state.set_state(AnonymousStates.waiting_for_message)


@router.message(AnonymousStates.waiting_for_message)
async def process_anon(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    save_anon_message(message.from_user.id, text)
    formatted = f"У вас анонимное сообщение: {text}"
    admin_ids = get_all_user_ids_by_role('admin')
    for admin_id in admin_ids:
        await bot.send_message(admin_id, formatted)
    await message.reply("Сообщение отправлено анонимно!")
    await state.clear()


@router.message(Command("events"))
async def get_events(message: Message):
    events = get_all_events()
    if not events:
        await message.reply("Событий пока нет.")
        return
    for _, planned_at, place, theme in events:
        formatted = f"📅 {planned_at}\n📍 {place}\n🎯 {theme}"
        await message.reply(formatted)
