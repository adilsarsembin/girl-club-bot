from datetime import datetime

from aiogram import Bot, Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommandScopeChat, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from database.anonymous import add_anonymous_message
from database.events import get_all_events
from database.photos import get_random_photo
from database.quotes import get_random_quote
from database.users import add_user, get_all_user_ids_by_role
from filters import IsAdmin
from logging_config import get_logger
from states.anonymous import AnonymousStates

logger = get_logger(__name__)

router = Router()

user_commands = [
    types.BotCommand(command="start", description="Запустить бота"),
    types.BotCommand(command="help", description="Показать доступные команды"),
    types.BotCommand(command="motivation", description="Получить вдохновение"),
    types.BotCommand(command="events", description="Посмотреть предстоящие события"),
    types.BotCommand(command="anonymous_message", description="Отправить анонимное сообщение"),
]
admin_commands = user_commands + [
    types.BotCommand(command="manage_quotes", description="Управление цитатами"),
    types.BotCommand(command="manage_photos", description="Управление фотографиями"),
    types.BotCommand(command="manage_events", description="Управление событиями"),
    types.BotCommand(command="send_all", description="Отправить всем")
]

@router.message(CommandStart())
async def send_welcome(message: types.Message, bot: Bot):
    """
    Handler for the /start command. This is for all users.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    logger.info(f"User {user_id} (@{username}) started the bot")

    await message.reply("🌸 Привет, дорогая! 🌸\n\nДобро пожаловать в наш уютный GirlClub! 💖\nЗдесь мы делимся вдохновением и поддержкой! ✨")

    admin_command = IsAdmin()
    is_admin = await admin_command(message)
    role = 'admin' if is_admin else 'user'

    if add_user(user_id, message.from_user.username, message.from_user.first_name, role):
        logger.info(f"New user registered: {user_id} (@{username}) as {role}")
    else:
        logger.debug(f"Existing user accessed bot: {user_id} (@{username})")

    if is_admin:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
        logger.debug(f"Admin commands set for user {user_id}")
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
        logger.debug(f"User commands set for user {user_id}")


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
            if cmd.command != "help":
                help_text += f"✨ /{cmd.command} - {cmd.description}\n"

        help_text += "\n👑 <b>Управление клубом:</b>\n"
        help_text += "🌟 /manage_quotes - Управление цитатами мудрости\n"
        help_text += "🌟 /manage_photos - Управление вдохновляющими фотографиями\n"
        help_text += "🌟 /manage_events - Управление событиями клуба\n"
        help_text += "🌟 /send_all - Отправить сообщение всем участницам\n"

        help_text += "\n💖 <i>Ты делаешь наш клуб прекрасным местом! Спасибо! 🌹</i>"
    else:
        help_text += "💕 <b>Мои возможности для тебя:</b>\n"
        for cmd in user_commands:
            help_text += f"✨ /{cmd.command} - {cmd.description}\n"

        help_text += "\n💖 <i>Я здесь, чтобы поддерживать и вдохновлять тебя! 🌸</i>"

    await message.reply(help_text, parse_mode="HTML")


@router.message(Command("motivation"))
async def cmd_motivation(message: Message):
    """
    Handler for the /motivation command. Shows options for quotes or photos.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    logger.info(f"User {user_id} (@{username}) requested motivation menu")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💭 Цитата мудрости", callback_data="motivation:quote")],
        [InlineKeyboardButton(text="📸 Вдохновляющая фотография", callback_data="motivation:photo")]
    ])

    await message.reply(
        "🌟 <b>Что тебя вдохновит сегодня?</b>\n\n💕 Выбери, что хочешь получить: мудрую цитату или красивую фотографию ✨",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("motivation:"))
async def process_motivation_choice(callback: CallbackQuery):
    """
    Handler for motivation type selection.
    """
    user_id = callback.from_user.id
    username = callback.from_user.username or "no_username"
    choice = callback.data.split(":")[1]

    logger.info(f"User {user_id} (@{username}) selected motivation type: {choice}")

    if choice == "quote":
        quote = get_random_quote()
        if quote:
            logger.debug(f"Sent quote to user {user_id}")
            await callback.message.edit_text(
                f"💖 <b>Мудрая мысль для тебя:</b>\n\n<i>{quote}</i>\n\n✨ Пусть она согреет твое сердце! 🌸",
                parse_mode="HTML"
            )
        else:
            logger.warning(f"No quotes available for user {user_id}")
            await callback.message.edit_text(
                "💕 <i>Цитат пока нет, но скоро появятся новые вдохновляющие слова!</i> ✨",
                parse_mode="HTML"
            )

    elif choice == "photo":
        photo = get_random_photo()
        if not photo:
            logger.warning(f"No photos available for user {user_id}")
            await callback.message.edit_text(
                "🌸 <b>Милая, фотографии скоро появятся!</b>\n\n📸 Пока администраторы готовят вдохновляющие картинки для тебя 💖",
                parse_mode="HTML"
            )
            return

        logger.debug(f"Sent photo {photo['id']} to user {user_id}")
        caption = "💕 <b>Вдохновляющая картинка специально для тебя!</b> ✨"
        if photo['caption']:
            caption += f"\n\n💭 {photo['caption']}"
        caption += "\n\n🌟 Пусть она наполнит тебя силой и красотой!"

        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo['file_id'],
            caption=caption,
            parse_mode="HTML"
        )

    await callback.answer()


@router.message(Command("anonymous_message"))
async def cmd_anon(message: Message, state: FSMContext):
    await message.reply("💌 <b>Анонимное послание</b>\n\nНапиши свои мысли, и они дойдут до администраторов клуба. Мы внимательно прочитаем каждое сообщение! 💕", parse_mode="HTML")
    await state.set_state(AnonymousStates.waiting_for_message)


@router.message(AnonymousStates.waiting_for_message)
async def process_anon(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"
    text = message.text

    logger.info(f"User {user_id} (@{username}) sent anonymous message")

    if add_anonymous_message(user_id, text):
        logger.info(f"Anonymous message saved from user {user_id}")
    else:
        logger.error(f"Failed to save anonymous message from user {user_id}")

    formatted = f"💌 <b>Новое анонимное послание:</b>\n\n💭 {text}\n\nОт участницы клуба ✨"
    admin_ids = get_all_user_ids_by_role('admin')

    sent_count = 0
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, formatted, parse_mode="HTML")
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send anonymous message to admin {admin_id}: {e}")

    logger.info(f"Anonymous message forwarded to {sent_count}/{len(admin_ids)} admins")

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
        if isinstance(planned_at, datetime):
            formatted_date = planned_at.strftime('%d.%m.%Y в %H:%M')
        else:
            try:
                event_dt = datetime.strptime(str(planned_at), '%Y-%m-%d %H:%M:%S')
                formatted_date = event_dt.strftime('%d.%m.%Y в %H:%M')
            except:
                formatted_date = str(planned_at)

        formatted = f"🎉 <b>{theme}</b>\n📅 {formatted_date}\n📍 {place}\n\n✨ Ждем именно тебя!"
        await message.reply(formatted, parse_mode="HTML")
