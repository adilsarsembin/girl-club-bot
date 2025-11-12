from datetime import date, datetime, timedelta

from aiogram import Router, Bot, F
from logging_config import get_logger

logger = get_logger(__name__)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from database.events import add_event, delete_event, get_all_events
from database.photos import add_photo, get_all_photos, delete_photo, get_photo_by_id
from database.quotes import add_quote, get_all_quotes, delete_quote
from database.anonymous import get_all_anonymous_messages, delete_anonymous_message, reply_to_anonymous_message, get_anonymous_message_by_id
from database.users import get_all_user_ids_by_role
from filters import IsAdmin
from jobs import schedule_reminder
from states.add_event import AddEventStates
from states.add_photo import AddPhotoStates
from states.add_quote import AddQuoteStates
from states.anonymous import AnonymousStates
from states.send_all import SendAllStates

router = Router()


@router.message(Command("add_event"), IsAdmin())
async def cmd_add_event(message: Message):
    markup = await SimpleCalendar().start_calendar()
    await message.reply("📅 <b>Давай создадим чудесное событие!</b>\n\nВыбери дату, когда соберемся вместе 💕", reply_markup=markup, parse_mode="HTML")


@router.callback_query(SimpleCalendarCallback.filter())
async def process_date_selection(callback: CallbackQuery, state: FSMContext, callback_data: SimpleCalendarCallback):
    result, selected_date = await SimpleCalendar().process_selection(callback, callback_data)
    if result:
        await state.update_data(selected_date=selected_date.strftime('%Y-%m-%d'))
        await callback.message.edit_text(f"✨ Отличная дата: {selected_date.strftime('%d.%m.%Y')}\n\n⏰ Теперь укажи время в формате ЧЧ:ММ\n\n💕 Например: 14:30 или 19:00", parse_mode="HTML")
        await state.set_state(AddEventStates.waiting_for_time)
    await callback.answer()


@router.message(StateFilter(AddEventStates.waiting_for_time))
async def process_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    data = await state.get_data()
    try:
        full_dt = datetime.strptime(f"{data['selected_date']} {time_str}", '%Y-%m-%d %H:%M')
        await state.update_data(full_datetime=full_dt.strftime('%Y-%m-%d %H:%M:%S'))
        await message.reply("🎯 <b>Какая замечательная тема события?</b>\n\n💭 Расскажи, чем будем заниматься! ✨", parse_mode="HTML")
        await state.set_state(AddEventStates.waiting_for_theme)
    except ValueError:
        await message.reply("⏰ <b>Ой, формат времени не совсем правильный</b>\n\n💡 Используй формат ЧЧ:ММ\n\n🌸 Например: 14:30 (два часа дня) или 19:00 (семь вечера)", parse_mode="HTML")


@router.message(StateFilter(AddEventStates.waiting_for_theme))
async def process_theme(message: Message, state: FSMContext):
    await state.update_data(theme=message.text.strip())
    await message.reply("📍 <b>Где состоится наша встреча?</b>\n\n🏠 Укажи адрес или название места 💕", parse_mode="HTML")
    await state.set_state(AddEventStates.waiting_for_place)


@router.message(StateFilter(AddEventStates.waiting_for_place))
async def process_place(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    place = message.text.strip()
    event_id = add_event(data['full_datetime'], data['theme'], place)
    if event_id:
        await schedule_reminder(bot, data['full_datetime'], event_id, data['theme'], place)
        await message.reply(f"🎉 <b>Ура! Событие создано!</b>\n\n📅 {data['full_datetime']}\n🎯 {data['theme']}\n📍 {place}\n\n💕 Все участницы получат напоминание за 24 часа!\n\n✨ Спасибо, что делаешь наш клуб таким замечательным!", parse_mode="HTML")

        # Return to main menu after successful event creation
        from handlers.user import is_admin_user, send_main_menu
        is_admin = await is_admin_user(message)
        await send_main_menu(message, is_admin)
    else:
        await message.reply("💔 <b>Ой, что-то пошло не так</b>\n\n❌ Не удалось добавить событие. Попробуй еще раз или обратись к администратору 💕", parse_mode="HTML")
        return

    await state.clear()


@router.message(Command("add_quote"), IsAdmin())
async def cmd_add_quote(message: Message, state: FSMContext):
    await message.reply("💭 <b>Какая мудрая цитата тебя вдохновила?</b>\n\n✨ Поделись ею с участницами клуба! 💕", parse_mode="HTML")
    await state.set_state(AddQuoteStates.waiting_for_quote)


@router.message(AddQuoteStates.waiting_for_quote)
async def process_quote(message: Message, state: FSMContext):
    text = message.text.strip()
    admin_id = message.from_user.id
    admin_username = message.from_user.username or "no_username"

    if add_quote(text):
        logger.info(f"Admin {admin_id} (@{admin_username}) added quote")
        await message.reply("💖 <b>Прекрасная цитата добавлена!</b>\n\n✨ Теперь она будет вдохновлять участниц клуба!\n\n🌸 Спасибо за твою заботу! 💕", parse_mode="HTML")

        # Return to main menu after successful quote addition
        from handlers.user import is_admin_user, send_main_menu
        is_admin = await is_admin_user(message)
        await send_main_menu(message, is_admin)
    else:
        logger.error(f"Failed to add quote for admin {admin_id}")
        await message.reply("💔 <b>Ой, что-то пошло не так</b>\n\n❌ Не удалось добавить цитату. Попробуй еще раз 💕", parse_mode="HTML")
        return

    await state.clear()


@router.message(Command("list_quotes"), IsAdmin())
async def cmd_list_quotes(message: Message):
    """
    Handler for the /list_quotes command. Shows all quotes with their IDs.
    """
    quotes = get_all_quotes()
    if not quotes:
        await message.reply("📝 Цитат пока нет в базе данных.")
        return

    response = "📝 <b>Все цитаты в базе данных:</b>\n\n"
    for quote_id, text, created_at in quotes:
        truncated_text = text[:100] + "..." if len(text) > 100 else text
        response += f"🆔 <b>{quote_id}</b> - {truncated_text}\n📅 {created_at}\n\n"

    if len(response) > 4000:
        parts = []
        current_part = "📝 <b>Все цитаты в базе данных:</b>\n\n"
        for quote_id, text, created_at in quotes:
            truncated_text = text[:100] + "..." if len(text) > 100 else text
            new_line = f"🆔 <b>{quote_id}</b> - {truncated_text}\n📅 {created_at}\n\n"
            if len(current_part + new_line) > 4000:
                parts.append(current_part)
                current_part = "📝 <b>Продолжение:</b>\n\n" + new_line
            else:
                current_part += new_line
        parts.append(current_part)

        for part in parts:
            await message.reply(part, parse_mode="HTML")
    else:
        await message.reply(response, parse_mode="HTML")


@router.message(Command("delete_quote"), IsAdmin())
async def cmd_delete_quote(message: Message):
    """
    Handler for the /delete_quote command. Shows inline keyboard for quote selection.
    """
    quotes = get_all_quotes()
    if not quotes:
        await message.reply("📝 Цитат для удаления нет.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for quote_id, text, created_at in quotes:
        truncated_text = text[:50] + "..." if len(text) > 50 else text
        keyboard.inline_keyboard.append([InlineKeyboardButton(
            text=f"🆔{quote_id}: {truncated_text}", callback_data=f"del_quote:{quote_id}"
        )])

    await message.reply("🗑️ <b>Выберите цитату для удаления:</b>", reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_quote:"))
async def process_delete_quote(callback: CallbackQuery):
    """
    Handler for processing quote deletion via inline keyboard.
    """
    quote_id = int(callback.data.split(":")[1])

    # Get quote info before deletion
    quotes = get_all_quotes()
    quote_info = next((q for q in quotes if q[0] == quote_id), None)

    if not quote_info:
        await callback.message.edit_text("❌ Цитата не найдена.")
        await callback.answer()
        return

    # Delete the quote
    if delete_quote(quote_id):
        truncated_text = quote_info[1][:50] + "..." if len(quote_info[1]) > 50 else quote_info[1]
        await callback.message.edit_text(f"✅ Цитата успешно удалена!\n\n💬 Текст: {truncated_text}")

        # Return to main menu after successful deletion
        from handlers.user import is_admin_user, send_main_menu
        is_admin = await is_admin_user(callback)
        await send_main_menu(callback.message, is_admin)
    else:
        await callback.message.edit_text("❌ Ошибка при удалении цитаты.")

    await callback.answer()


@router.message(Command("add_photo"), IsAdmin())
async def cmd_add_photo(message: Message, state: FSMContext):
    """
    Handler for the /add_photo command. Initiates photo upload process.
    """
    await message.reply("🌟 <b>Давай добавим вдохновляющую фотографию!</b>\n\n📸 Отправь красивую картинку, которая поднимет настроение участницам клуба 💕", parse_mode="HTML")
    await state.set_state(AddPhotoStates.waiting_for_photo)


@router.message(AddPhotoStates.waiting_for_photo)
async def process_photo_upload(message: Message, state: FSMContext):
    """
    Handler for processing photo upload.
    """
    try:
        file_id = None
        file_unique_id = None
        filename = None

        if message.photo:
            photo = message.photo[-1]
            file_id = photo.file_id
            file_unique_id = photo.file_unique_id
        elif (
            message.document
            and message.document.mime_type
            and message.document.mime_type.startswith("image/")
        ):
            doc = message.document
            file_id = doc.file_id
            file_unique_id = doc.file_unique_id
            filename = doc.file_name
        else:
            await message.reply(
                "📸 <b>Мне нужна фотография!</b>\n\n"
                "💕 Отправь изображение как фото или выбери «Отправить как фото», если загружаешь файл. ✨",
                parse_mode="HTML"
            )
            return

        if not file_id or not file_unique_id:
            await message.reply(
                "💔 <b>Ошибка обработки изображения</b>\n\n"
                "❌ Попробуй отправить фотографию еще раз или выбери другую. 💕",
                parse_mode="HTML"
            )
            return

        await state.update_data(
            file_id=file_id,
            file_unique_id=file_unique_id,
            filename=filename
        )

        await message.reply(
            "📝 <b>Хочешь добавить нежное описание к фото?</b>\n\n"
            "💭 Расскажи, что вдохновляет в этой картинке!\n\n"
            "✨ Или нажми /skip, если описание не нужно 💕",
            parse_mode="HTML"
        )
        await state.set_state(AddPhotoStates.waiting_for_caption)

    except Exception as e:
        logger.error(f"Error in photo upload: {e}")
        await message.reply(
            "💔 <b>Произошла ошибка при обработке фото</b>\n\n"
            "❌ Попробуй еще раз или обратись к администратору 💕",
            parse_mode="HTML"
        )
        await state.clear()


@router.message(AddPhotoStates.waiting_for_caption)
async def process_caption(message: Message, state: FSMContext):
    """
    Handler for processing photo caption.
    """
    try:
        data = await state.get_data()

        # Validate that we have photo data
        if not data or 'file_id' not in data:
            await message.reply("💔 <b>Ошибка сессии</b>\n\n❌ Данные фото не найдены. Начни заново с /add_photo 💕", parse_mode="HTML")
            await state.clear()
            return

        caption = None

        if message.text and not message.text.startswith('/'):
            caption = message.text.strip()
        elif message.text == "/skip":
            caption = None
        else:
            await message.reply("💭 <b>Расскажи о фото или пропусти</b>\n\n✨ Отправь текст описания или нажми /skip 💕", parse_mode="HTML")
            return

        # Add photo with or without caption
        photo_result = add_photo(
            file_id=data['file_id'],
            file_unique_id=data['file_unique_id'],
            filename=data.get('filename'),
            caption=caption,
            uploaded_by=message.from_user.id
        )

        if photo_result and photo_result > 0:
            admin_id = message.from_user.id
            admin_username = message.from_user.username or "no_username"

            if caption:
                logger.info(f"Admin {admin_id} (@{admin_username}) added photo with caption")
                await message.reply("🌟 <b>Чудесная фотография добавлена!</b>\n\n💖 С таким красивым описанием она точно вдохновит участниц!\n\n✨ Спасибо за твою заботу! 💕", parse_mode="HTML")
            else:
                logger.info(f"Admin {admin_id} (@{admin_username}) added photo without caption")
                await message.reply("🌸 <b>Прекрасная фотография добавлена!</b>\n\n💕 Она будет радовать участниц клуба!\n\n✨ Спасибо за твою заботу! 💖", parse_mode="HTML")

            # Return to main menu after successful photo addition
            from handlers.user import is_admin_user, send_main_menu
            is_admin = await is_admin_user(message)
            await send_main_menu(message, is_admin)
            await state.clear()
        else:
            logger.error(f"Failed to add photo for admin {message.from_user.id} - add_photo returned: {photo_result}")
            await message.reply("💔 <b>Не удалось сохранить фото</b>\n\n❌ Проверь подключение к базе данных и попробуй еще раз 💕", parse_mode="HTML")
            return

    except Exception as e:
        logger.error(f"Error in caption processing: {e}")
        await message.reply("💔 <b>Произошла ошибка</b>\n\n❌ Попробуй начать заново с /add_photo 💕", parse_mode="HTML")
        await state.clear()


@router.message(Command("list_photos"), IsAdmin())
async def cmd_list_photos(message: Message):
    """
    Handler for the /list_photos command. Shows all photos.
    """
    photos = get_all_photos()
    if not photos:
        await message.reply("📸 <b>Коллекция фотографий пока пустая</b>\n\n💕 Но скоро здесь появятся прекрасные вдохновляющие картинки! 🌟", parse_mode="HTML")
        return

    response = "📸 <b>Все фотографии в базе данных:</b>\n\n"
    for photo_id, file_id, filename, caption, uploaded_at in photos:
        if caption and caption.strip():
            display_name = f"📝 {caption.strip()[:40]}..." if len(caption.strip()) > 40 else f"📝 {caption.strip()}"
        elif filename:
            display_name = f"📄 {filename[:40]}..." if len(filename) > 40 else f"📄 {filename}"
        else:
            upload_date = str(uploaded_at).split()[0]
            display_name = f"📸 Фото от {upload_date}"

        response += f"🆔 <b>{photo_id}</b>\n{display_name}\n📅 {uploaded_at}\n\n"

    # Telegram has message length limits, so split if too long
    if len(response) > 4000:
        parts = []
        current_part = "📸 <b>Все фотографии в базе данных:</b>\n\n"
        for photo_id, file_id, filename, caption, uploaded_at in photos:
            # Create the same display name logic as above
            if caption and caption.strip():
                display_name = f"📝 {caption.strip()[:40]}..." if len(caption.strip()) > 40 else f"📝 {caption.strip()}"
            elif filename:
                display_name = f"📄 {filename[:40]}..." if len(filename) > 40 else f"📄 {filename}"
            else:
                upload_date = str(uploaded_at).split()[0]
                display_name = f"📸 Фото от {upload_date}"

            new_line = f"🆔 <b>{photo_id}</b>\n{display_name}\n📅 {uploaded_at}\n\n"
            if len(current_part + new_line) > 4000:
                parts.append(current_part)
                current_part = "📸 <b>Продолжение:</b>\n\n" + new_line
            else:
                current_part += new_line
        parts.append(current_part)

        for part in parts:
            await message.reply(part, parse_mode="HTML")
    else:
        await message.reply(response, parse_mode="HTML")


@router.message(Command("delete_photo"), IsAdmin())
async def cmd_delete_photo(message: Message):
    """
    Handler for the /delete_photo command. Shows inline keyboard for photo selection.
    """
    photos = get_all_photos()
    if not photos:
        await message.reply("📸 <b>Все фотографии в безопасности!</b>\n\n💕 Пока нет фотографий для удаления 🌸", parse_mode="HTML")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for photo_id, file_id, filename, caption, uploaded_at in photos:
        if caption and caption.strip():
            display_name = caption.strip()[:35] + "..." if len(caption.strip()) > 35 else caption.strip()
        elif filename:
            display_name = filename[:35] + "..." if len(filename) > 35 else filename
        else:
            upload_date = str(uploaded_at).split()[0]
            display_name = f"Фото от {upload_date}"

        keyboard.inline_keyboard.append([InlineKeyboardButton(
            text=f"🆔{photo_id}: {display_name}", callback_data=f"del_photo:{photo_id}"
        )])

    await message.reply("🗑️ <b>Выберите фотографию для удаления:</b>", reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_photo:"))
async def process_delete_photo(callback: CallbackQuery):
    """
    Handler for processing photo deletion via inline keyboard.
    """
    photo_id = int(callback.data.split(":")[1])

    # Get photo info before deletion
    photo = get_photo_by_id(photo_id)
    if not photo:
        await callback.message.edit_text("❌ Фотография не найдена.")
        await callback.answer()
        return

    # Delete the photo
    if delete_photo(photo_id):
        filename_display = photo['filename'] or "Без имени"
        await callback.message.edit_text(f"✅ Фотография удалена!\n\n📸 {filename_display}")

        # Return to main menu after successful deletion
        from handlers.user import is_admin_user, send_main_menu
        is_admin = await is_admin_user(callback)
        await send_main_menu(callback.message, is_admin)
    else:
        await callback.message.edit_text("❌ Ошибка при удалении фотографии.")

    await callback.answer()


# === NEW MANAGEMENT INTERFACE ===

@router.message(Command("manage_quotes"), IsAdmin())
async def cmd_manage_quotes(message: Message):
    """
    Handler for the /manage_quotes command. Shows quote management options.
    """
    admin_id = message.from_user.id
    admin_username = message.from_user.username or "no_username"

    logger.info(f"Admin {admin_id} (@{admin_username}) opened quotes management")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Добавить цитату", callback_data="quotes:add")],
        [InlineKeyboardButton(text="📝 Показать все цитаты", callback_data="quotes:list")],
        [InlineKeyboardButton(text="🗑️ Удалить цитату", callback_data="quotes:delete")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:back_to_main")]
    ])

    await message.reply(
        "💭 <b>Управление цитатами мудрости</b>\n\n💕 Выбери, что хочешь сделать с цитатами клуба ✨",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("manage_photos"), IsAdmin())
async def cmd_manage_photos(message: Message):
    """
    Handler for the /manage_photos command. Shows photo management options.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Добавить фотографию", callback_data="photos:add")],
        [InlineKeyboardButton(text="🖼️ Показать все фотографии", callback_data="photos:list")],
        [InlineKeyboardButton(text="🗑️ Удалить фотографию", callback_data="photos:delete")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:back_to_main")]
    ])

    await message.reply(
        "🌟 <b>Управление вдохновляющими фотографиями</b>\n\n💕 Выбери, что хочешь сделать с фото коллекцией ✨",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("manage_events"), IsAdmin())
async def cmd_manage_events(message: Message):
    """
    Handler for the /manage_events command. Shows event management options.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 Создать событие", callback_data="events:add")],
        [InlineKeyboardButton(text="📅 Показать все события", callback_data="events:list")],
        [InlineKeyboardButton(text="🗑️ Удалить событие", callback_data="events:delete")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:back_to_main")]
    ])

    await message.reply(
        "🎊 <b>Управление событиями клуба</b>\n\n💕 Выбери, что хочешь сделать с расписанием мероприятий ✨",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("quotes:"))
async def process_quotes_management(callback: CallbackQuery, state: FSMContext):
    """
    Handler for quotes management actions.
    """
    admin_id = callback.from_user.id
    admin_username = callback.from_user.username or "no_username"
    action = callback.data.split(":")[1]

    logger.info(f"Admin {admin_id} (@{admin_username}) selected quotes action: {action}")

    if action == "add":
        await callback.message.edit_text("💭 <b>Какая мудрая цитата тебя вдохновила?</b>\n\n✨ Поделись ею с участницами клуба! 💕", parse_mode="HTML")
        await state.set_state(AddQuoteStates.waiting_for_quote)

    elif action == "list":
        quotes = get_all_quotes()
        if not quotes:
            await callback.message.edit_text("📝 <b>Цитат пока нет в базе данных</b>\n\n💕 Но скоро появятся прекрасные мудрые слова! ✨", parse_mode="HTML")
            return

        response = "📝 <b>Все цитаты в базе данных:</b>\n\n"
        for quote_id, text, created_at in quotes:
            if text and len(text) > 50:
                display_name = f"💭 {text[:50]}..."
            elif text:
                display_name = f"💭 {text}"
            else:
                display_name = "💭 Без текста"

            response += f"🆔 <b>{quote_id}</b>\n{display_name}\n📅 {created_at}\n\n"

        if len(response) > 4000:
            await callback.message.edit_text("📝 <b>Слишком много цитат для отображения</b>\n\n💕 Используй индивидуальные команды для управления! ✨", parse_mode="HTML")
        else:
            await callback.message.edit_text(response, parse_mode="HTML")

    elif action == "delete":
        quotes = get_all_quotes()
        if not quotes:
            await callback.message.edit_text("📝 <b>Цитат для удаления нет</b>\n\n💕 Все цитаты в безопасности! 🌸", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for quote_id, text, created_at in quotes:
            if text and len(text) > 50:
                display_name = text[:50] + "..."
            elif text:
                display_name = text
            else:
                display_name = "Без текста"

            keyboard.inline_keyboard.append([InlineKeyboardButton(
                text=f"🆔{quote_id}: {display_name}", callback_data=f"del_quote:{quote_id}"
            )])

        await callback.message.edit_text("🗑️ <b>Выберите цитату для удаления:</b>", reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data.startswith("photos:"))
async def process_photos_management(callback: CallbackQuery, state: FSMContext):
    """
    Handler for photos management actions.
    """
    action = callback.data.split(":")[1]

    if action == "add":
        await callback.message.edit_text("🌟 <b>Давай добавим вдохновляющую фотографию!</b>\n\n📸 Отправь красивую картинку, которая поднимет настроение участницам клуба 💕", parse_mode="HTML")
        await state.set_state(AddPhotoStates.waiting_for_photo)

    elif action == "list":
        photos = get_all_photos()
        if not photos:
            await callback.message.edit_text("📸 <b>Коллекция фотографий пока пустая</b>\n\n💕 Но скоро здесь появятся прекрасные вдохновляющие картинки! 🌟", parse_mode="HTML")
            return

        response = "📸 <b>Все фотографии в базе данных:</b>\n\n"
        for photo_id, file_id, filename, caption, uploaded_at in photos:
            if caption and caption.strip():
                display_name = f"📝 {caption.strip()[:40]}..." if len(caption.strip()) > 40 else f"📝 {caption.strip()}"
            elif filename:
                display_name = f"📄 {filename[:40]}..." if len(filename) > 40 else f"📄 {filename}"
            else:
                upload_date = str(uploaded_at).split()[0]
                display_name = f"📸 Фото от {upload_date}"

            response += f"🆔 <b>{photo_id}</b>\n{display_name}\n📅 {uploaded_at}\n\n"

        if len(response) > 4000:
            await callback.message.edit_text("📸 <b>Слишком много фотографий для отображения</b>\n\n💕 Используй индивидуальные команды для управления! ✨", parse_mode="HTML")
        else:
            await callback.message.edit_text(response, parse_mode="HTML")

    elif action == "delete":
        photos = get_all_photos()
        if not photos:
            await callback.message.edit_text("📸 <b>Все фотографии в безопасности!</b>\n\n💕 Пока нет фотографий для удаления 🌸", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for photo_id, file_id, filename, caption, uploaded_at in photos:
            if caption and caption.strip():
                display_name = caption.strip()[:35] + "..." if len(caption.strip()) > 35 else caption.strip()
            elif filename:
                display_name = filename[:35] + "..." if len(filename) > 35 else filename
            else:
                upload_date = str(uploaded_at).split()[0]
                display_name = f"Фото от {upload_date}"

            keyboard.inline_keyboard.append([InlineKeyboardButton(
                text=f"🆔{photo_id}: {display_name}", callback_data=f"del_photo:{photo_id}"
            )])

        await callback.message.edit_text("🗑️ <b>Выберите фотографию для удаления:</b>", reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data.startswith("events:"))
async def process_events_management(callback: CallbackQuery, state: FSMContext):
    """
    Handler for events management actions.
    """
    action = callback.data.split(":")[1]

    if action == "add":
        markup = await SimpleCalendar().start_calendar()
        await callback.message.edit_text("📅 <b>Давай создадим чудесное событие!</b>\n\nВыбери дату, когда соберемся вместе 💕", reply_markup=markup, parse_mode="HTML")

    elif action == "list":
        events = get_all_events()
        if not events:
            await callback.message.edit_text("📅 <b>Событий пока нет в расписании</b>\n\n💕 Но скоро появятся интересные мероприятия! 🌟", parse_mode="HTML")
            return

        response = "🎊 <b>Все события в расписании:</b>\n\n"
        for event_id, planned_at, theme, place in events:
            if isinstance(planned_at, datetime):
                formatted_date = planned_at.strftime('%d.%m.%Y в %H:%M')
            else:
                try:
                    event_dt = datetime.strptime(str(planned_at), '%Y-%m-%d %H:%M:%S')
                    formatted_date = event_dt.strftime('%d.%m.%Y в %H:%M')
                except:
                    formatted_date = str(planned_at)

            response += f"🆔 <b>{event_id}</b>\n🎉 {theme}\n📅 {formatted_date}\n📍 {place}\n\n"

        if len(response) > 4000:
            await callback.message.edit_text("🎊 <b>Слишком много событий для отображения</b>\n\n💕 Используй индивидуальные команды для управления! ✨", parse_mode="HTML")
        else:
            await callback.message.edit_text(response, parse_mode="HTML")

    elif action == "delete":
        events = get_all_events()
        if not events:
            await callback.message.edit_text("📅 <b>Все события в расписании!</b>\n\n💕 Пока нет событий для удаления 🌸", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for event_id, planned_at, theme, place in events:
            if isinstance(planned_at, datetime):
                display_date = planned_at.strftime('%d.%m %H:%M')
            else:
                try:
                    event_dt = datetime.strptime(str(planned_at), '%Y-%m-%d %H:%M:%S')
                    display_date = event_dt.strftime('%d.%m %H:%M')
                except:
                    display_date = str(planned_at).split()[0] if ' ' in str(planned_at) else str(planned_at)

            keyboard.inline_keyboard.append([InlineKeyboardButton(
                text=f"{display_date} - {theme[:30]}...", callback_data=f"del_event:{event_id}"
            )])

        await callback.message.edit_text("🗑️ <b>Выбери событие для удаления:</b>\n\n💕 Выбери то, которое нужно отменить 🌸", reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


@router.message(Command("send_all"), IsAdmin())
async def cmd_send_all(message: Message, state: FSMContext, bot: Bot):
    admin_id = message.from_user.id
    admin_username = message.from_user.username or "no_username"

    logger.info(f"Admin {admin_id} (@{admin_username}) initiated broadcast message")

    await message.reply("💌 <b>Сообщение для всех участниц</b>\n\n✨ Напиши что-то теплое и вдохновляющее для нашего клуба! 💕\n\nВсе получат твое послание с любовью! 🌸", parse_mode="HTML")
    await state.set_state(SendAllStates.waiting_for_message)


@router.message(SendAllStates.waiting_for_message)
async def process_send_all(message: Message, state: FSMContext, bot: Bot):
    admin_id = message.from_user.id
    admin_username = message.from_user.username or "no_username"
    text = message.text

    logger.info(f"Admin {admin_id} (@{admin_username}) sending broadcast message")

    user_ids = get_all_user_ids_by_role('user')
    sent_count = 0
    failed_count = 0

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to send broadcast to user {user_id}: {e}")

    logger.info(f"Broadcast completed: {sent_count} successful, {failed_count} failed, total users: {len(user_ids)}")

    await message.reply(f"💌 <b>Сообщение отправлено!</b>\n\n✨ Дошло до {sent_count} из {len(user_ids)} участниц\n\n💕 Спасибо, что заботишься о нашем клубе! 🌸", parse_mode="HTML")
    await message.answer("⬅️ Возвращаемся в меню. Нажми кнопку ниже или команду /menu.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:back_to_main")]]
    ), parse_mode="HTML")
    await state.clear()


@router.message(Command("delete_event"), IsAdmin())
async def cmd_delete_event(message: Message):
    events = get_all_events()
    if not events:
        await message.reply("📅 <b>Все события в расписании!</b>\n\n💕 Пока нет событий для удаления 🌸", parse_mode="HTML")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for event_id, planned_at, theme, place in events:
        keyboard.inline_keyboard.append([InlineKeyboardButton(
            text=f"{planned_at} - {theme}", callback_data=f"del_event:{event_id}"
        )])
    await message.reply("🗑️ <b>Выбери событие для удаления:</b>\n\n💕 Выбери то, которое нужно отменить 🌸", reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_event:"))
async def process_delete_event(callback: CallbackQuery):
    event_id = int(callback.data.split(":")[1])
    if delete_event(event_id):
        await callback.message.edit_text("✅ <b>Событие отменено</b>\n\n💕 Участницы будут оповещены об изменениях 🌸", parse_mode="HTML")

        # Return to main menu after successful deletion
        from handlers.user import is_admin_user, send_main_menu
        is_admin = await is_admin_user(callback)
        await send_main_menu(callback.message, is_admin)
    else:
        await callback.message.edit_text("💔 <b>Ой, не получилось отменить событие</b>\n\n❌ Попробуй еще раз или обратись к администратору 💕", parse_mode="HTML")
    await callback.answer()


# === ANONYMOUS MESSAGES MANAGEMENT ===

@router.message(Command("manage_anonymous"), IsAdmin())
async def cmd_manage_anonymous(message: Message):
    """
    Handler for the /manage_anonymous command. Shows anonymous message management options.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Просмотреть сообщения", callback_data="anon:list")],
        [InlineKeyboardButton(text="🗑️ Удалить сообщения", callback_data="anon:delete")]
    ])

    await message.reply(
        "💌 <b>Управление анонимными сообщениями</b>\n\n💕 Выбери, что хочешь сделать с сообщениями участниц ✨",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("anon:"))
async def process_anonymous_management(callback: CallbackQuery, state: FSMContext):
    """
    Handler for anonymous message management actions.
    """
    action = callback.data.split(":")[1]

    if action == "list":
        messages = get_all_anonymous_messages()
        if not messages:
            await callback.message.edit_text("📨 <b>Анонимных сообщений пока нет</b>\n\n💕 Участницы еще не отправляли анонимные послания ✨", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for msg_id, user_id, message_text, created_at, reply, replied_by, replied_at in messages:
            # Truncate message for display
            display_text = message_text[:40] + "..." if len(message_text) > 40 else message_text
            status = "✅ Отвечено" if reply else "⏳ Ожидает ответа"

            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"💌 {display_text} - {status}",
                    callback_data=f"anon_view:{msg_id}"
                )
            ])

        await callback.message.edit_text("📨 <b>Все анонимные сообщения:</b>\n\n💕 Нажми на сообщение, чтобы просмотреть или ответить ✨", reply_markup=keyboard, parse_mode="HTML")

    elif action == "delete":
        messages = get_all_anonymous_messages()
        if not messages:
            await callback.message.edit_text("🗑️ <b>Сообщений для удаления нет</b>\n\n💕 Все сообщения в безопасности! 🌸", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for msg_id, user_id, message_text, created_at, reply, replied_by, replied_at in messages:
            display_text = message_text[:30] + "..." if len(message_text) > 30 else message_text
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🗑️ {display_text}",
                    callback_data=f"anon_del:{msg_id}"
                )
            ])

        await callback.message.edit_text("🗑️ <b>Выбери сообщение для удаления:</b>\n\n💕 Выбери то, которое нужно удалить 🌸", reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data.startswith("anon_view:"))
async def process_view_anonymous_message(callback: CallbackQuery, state: FSMContext):
    """
    Handler for viewing and replying to anonymous messages.
    """
    message_id = int(callback.data.split(":")[1])
    message_data = get_anonymous_message_by_id(message_id)

    if not message_data:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return

    response = f"💌 <b>Анонимное сообщение #{message_data['id']}</b>\n\n"
    response += f"💭 <b>Сообщение:</b> {message_data['message']}\n"
    response += f"📅 <b>Отправлено:</b> {message_data['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"

    if message_data['reply']:
        response += f"💕 <b>Ваш ответ:</b> {message_data['reply']}\n"
        response += f"📅 <b>Ответ отправлен:</b> {message_data['replied_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        response += "✅ <b>Это сообщение уже отвечено</b>"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="anon:list")]
        ])
    else:
        response += "⏳ <b>Это сообщение ожидает ответа</b>\n\n💕 Хотите ответить участнице?"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💌 Ответить", callback_data=f"anon_reply:{message_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="anon:list")]
        ])

    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("anon_reply:"))
async def process_reply_anonymous_message(callback: CallbackQuery, state: FSMContext):
    """
    Handler for starting reply to anonymous message.
    """
    message_id = int(callback.data.split(":")[1])

    # Store message ID in state for reply processing
    await state.update_data(reply_message_id=message_id)

    await callback.message.edit_text(
        "💌 <b>Напишите ваш ответ</b>\n\n✨ Участница получит ваше сообщение анонимно 💕\n\n💭 Напишите теплый и поддерживающий ответ!",
        parse_mode="HTML"
    )

    await state.set_state(AnonymousStates.waiting_for_reply)
    await callback.answer()


@router.message(AnonymousStates.waiting_for_reply)
async def process_anonymous_reply(message: Message, state: FSMContext, bot: Bot):
    """
    Handler for processing admin reply to anonymous message.
    """
    data = await state.get_data()
    message_id = data.get('reply_message_id')

    if not message_id:
        await message.reply("💔 <b>Ошибка</b>\n\n❌ Не удалось найти сообщение для ответа 💕", parse_mode="HTML")
        await state.clear()
        return

    reply_text = message.text.strip()

    # Save reply to database
    if reply_to_anonymous_message(message_id, reply_text, message.from_user.id):
        # Get original message to find user
        original_message = get_anonymous_message_by_id(message_id)
        if original_message:
            try:
                # Send reply to the original user
                user_response = f"💌 <b>Ответ на ваше анонимное послание</b>\n\n💕 Администратор прочитал ваше сообщение и ответил:\n\n💭 <i>{reply_text}</i>\n\n✨ Спасибо, что доверяете нам! 🌸"
                await bot.send_message(original_message['user_id'], user_response, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Failed to send reply to user {original_message['user_id']}: {e}")

        await message.reply("✅ <b>Ответ отправлен!</b>\n\n💕 Участница получила ваш теплый ответ ✨", parse_mode="HTML")

        # Return to main menu
        from handlers.user import is_admin_user, send_main_menu
        is_admin = await is_admin_user(message)
        await send_main_menu(message, is_admin)
    else:
        await message.reply("💔 <b>Ошибка при сохранении ответа</b>\n\n❌ Попробуйте еще раз 💕", parse_mode="HTML")

    await state.clear()


@router.callback_query(F.data.startswith("anon_del:"))
async def process_delete_anonymous_message(callback: CallbackQuery):
    """
    Handler for deleting anonymous messages.
    """
    message_id = int(callback.data.split(":")[1])

    if delete_anonymous_message(message_id):
        await callback.message.edit_text("✅ <b>Анонимное сообщение удалено</b>\n\n💕 Сообщение успешно удалено из системы 🌸", parse_mode="HTML")

        # Return to main menu after successful deletion
        from handlers.user import is_admin_user, send_main_menu
        is_admin = await is_admin_user(callback)
        await send_main_menu(callback.message, is_admin)
    else:
        await callback.message.edit_text("💔 <b>Ошибка при удалении</b>\n\n❌ Не удалось удалить сообщение 💕", parse_mode="HTML")

    await callback.answer()
