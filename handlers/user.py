from aiogram import Bot, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommandScopeChat, Message

from database.anonymous import save_anon_message
from database.events import get_all_events
from database.photos import get_random_photo
from database.quotes import get_random_quote
from database.users import add_user, get_all_user_ids_by_role
from filters import IsAdmin
from states.anonymous import AnonymousStates

router = Router()

user_commands = [
    types.BotCommand(command="start", description="Запустить бота"),
    types.BotCommand(command="help", description="Показать доступные команды"),
    types.BotCommand(command="quote", description="Получить случайную цитату"),
    types.BotCommand(command="photo", description="Получить мотивационную фотографию"),
    types.BotCommand(command="anonymous_message", description="Отправить анонимное сообщение"),
    types.BotCommand(command="events", description="Посмотреть предстоящие события"),
]
admin_commands = user_commands + [
    types.BotCommand(command="add_event", description="Добавить событие"),
    types.BotCommand(command="add_quote", description="Добавить цитату"),
    types.BotCommand(command="add_photo", description="Добавить фотографию"),
    types.BotCommand(command="list_quotes", description="Показать все цитаты"),
    types.BotCommand(command="list_photos", description="Показать все фотографии"),
    types.BotCommand(command="delete_quote", description="Удалить цитату"),
    types.BotCommand(command="delete_photo", description="Удалить фотографию"),
    types.BotCommand(command="send_all", description="Отправить всем"),
    types.BotCommand(command="delete_event", description="Удалить событие")
]

@router.message(CommandStart())
async def send_welcome(message: types.Message, bot: Bot):
    """
    Handler for the /start command. This is for all users.
    """
    await message.reply("🌸 Привет, дорогая! 🌸\n\nДобро пожаловать в наш уютный GirlClub! 💖\nЗдесь мы делимся вдохновением и поддержкой! ✨")
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

    help_text = "🌸 <b>Дорогая, вот что я умею для тебя:</b> ✨\n\n"

    if is_admin:
        help_text += "💕 <b>Команды для всех участниц:</b>\n"
        for cmd in user_commands:
            if cmd.command != "help":  # Skip help command in list
                help_text += f"✨ /{cmd.command} - {cmd.description}\n"

        help_text += "\n👑 <b>Специальные команды для администратора:</b>\n"
        for cmd in admin_commands[len(user_commands):]:  # Get only admin-specific commands
            help_text += f"🌟 /{cmd.command} - {cmd.description}\n"

        help_text += "\n💖 <i>Ты делаешь наш клуб прекрасным местом! Спасибо! 🌹</i>"
    else:
        help_text += "💕 <b>Мои возможности для тебя:</b>\n"
        for cmd in user_commands:
            help_text += f"✨ /{cmd.command} - {cmd.description}\n"

        help_text += "\n💖 <i>Я здесь, чтобы поддерживать и вдохновлять тебя! 🌸</i>"

    await message.reply(help_text, parse_mode="HTML")


@router.message(Command("quote"))
async def get_quote(message: types.Message):
    quote = get_random_quote()
    if quote:
        await message.reply(f"💖 <b>Мудрая мысль для тебя:</b>\n\n<i>{quote}</i>\n\n✨ Пусть она согреет твое сердце! 🌸", parse_mode="HTML")
    else:
        await message.reply("💕 <i>Цитат пока нет, но скоро появятся новые вдохновляющие слова!</i> ✨", parse_mode="HTML")


@router.message(Command("photo"))
async def get_photo(message: types.Message):
    """
    Handler for the /photo command. Sends a random motivational photo.
    """
    photo = get_random_photo()
    if not photo:
        await message.reply("🌸 <b>Милая, фотографии скоро появятся!</b>\n\n📸 Пока администраторы готовят вдохновляющие картинки для тебя 💖", parse_mode="HTML")
        return

    caption = "💕 <b>Вдохновляющая картинка специально для тебя!</b> ✨"
    if photo['caption']:
        caption += f"\n\n💭 {photo['caption']}"
    caption += "\n\n🌟 Пусть она наполнит тебя силой и красотой!"

    await message.reply_photo(
        photo=photo['file_id'],
        caption=caption,
        parse_mode="HTML"
    )


@router.message(Command("anonymous_message"))
async def cmd_anon(message: Message, state: FSMContext):
    await message.reply("💌 <b>Анонимное послание</b>\n\nНапиши свои мысли, и они дойдут до администраторов клуба. Мы внимательно прочитаем каждое сообщение! 💕", parse_mode="HTML")
    await state.set_state(AnonymousStates.waiting_for_message)


@router.message(AnonymousStates.waiting_for_message)
async def process_anon(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    save_anon_message(message.from_user.id, text)
    formatted = f"💌 <b>Новое анонимное послание:</b>\n\n💭 {text}\n\nОт участницы клуба ✨"
    admin_ids = get_all_user_ids_by_role('admin')
    for admin_id in admin_ids:
        await bot.send_message(admin_id, formatted, parse_mode="HTML")
    await message.reply("💕 <b>Спасибо за твое послание!</b>\n\n✨ Оно отправлено администраторам клуба. Мы ценим твою откровенность и заботу! 🌸", parse_mode="HTML")
    await state.clear()


@router.message(Command("events"))
async def get_events(message: Message):
    events = get_all_events()
    if not events:
        await message.reply("🌸 <b>Дорогая, скоро появятся новые события!</b>\n\n📅 Пока администраторы планируют интересные встречи для нашего клуба 💕\n\nСледи за обновлениями! ✨", parse_mode="HTML")
        return

    intro_message = "🌟 <b>Предстоящие события нашего клуба:</b>\n\n💕 Приходи, будет интересно и тепло! 🌸\n\n"
    await message.reply(intro_message, parse_mode="HTML")

    for _, planned_at, place, theme in events:
        # Format the date nicely
        try:
            from datetime import datetime
            event_dt = datetime.strptime(planned_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = event_dt.strftime('%d.%m.%Y в %H:%M')
        except:
            formatted_date = planned_at

        formatted = f"🎉 <b>{theme}</b>\n📅 {formatted_date}\n📍 {place}\n\n✨ Ждем именно тебя!"
        await message.reply(formatted, parse_mode="HTML")
