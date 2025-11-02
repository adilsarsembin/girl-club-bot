from datetime import date, timedelta, datetime

from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from database.events import add_event, delete_event, get_all_events
from database.photos import add_photo, get_all_photos, delete_photo, get_photo_by_id
from database.quotes import add_quote, get_all_quotes, delete_quote
from database.users import get_all_user_ids_by_role
from filters import IsAdmin
from jobs import schedule_reminder
from states.add_event import AddEventStates
from states.add_photo import AddPhotoStates
from states.add_quote import AddQuoteStates
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
    else:
        await message.reply("💔 <b>Ой, что-то пошло не так</b>\n\n❌ Не удалось добавить событие. Попробуй еще раз или обратись к администратору 💕", parse_mode="HTML")

    await state.clear()


@router.message(Command("add_quote"), IsAdmin())
async def cmd_add_quote(message: Message, state: FSMContext):
    await message.reply("💭 <b>Какая мудрая цитата тебя вдохновила?</b>\n\n✨ Поделись ею с участницами клуба! 💕", parse_mode="HTML")
    await state.set_state(AddQuoteStates.waiting_for_quote)


@router.message(AddQuoteStates.waiting_for_quote)
async def process_quote(message: Message, state: FSMContext):
    text = message.text.strip()
    if add_quote(text):
        await message.reply("💖 <b>Прекрасная цитата добавлена!</b>\n\n✨ Теперь она будет вдохновлять участниц клуба!\n\n🌸 Спасибо за твою заботу! 💕", parse_mode="HTML")
    else:
        await message.reply("💔 <b>Ой, что-то пошло не так</b>\n\n❌ Не удалось добавить цитату. Попробуй еще раз 💕", parse_mode="HTML")
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
    if not message.photo:
        await message.reply("📸 <b>Мне нужна фотография!</b>\n\n💕 Отправь картинку, которую хочешь добавить в коллекцию ✨", parse_mode="HTML")
        return

    # Get the largest photo size (best quality)
    photo = message.photo[-1]

    # Store photo info temporarily in state
    await state.update_data(
        file_id=photo.file_id,
        file_unique_id=photo.file_unique_id,
        filename=getattr(message.document, 'filename', None) if message.document else None
    )

    await message.reply("📝 <b>Хочешь добавить нежное описание к фото?</b>\n\n💭 Расскажи, что вдохновляет в этой картинке!\n\n✨ Или нажми /skip, если описание не нужно 💕", parse_mode="HTML")
    await state.set_state(AddPhotoStates.waiting_for_caption)


@router.message(AddPhotoStates.waiting_for_caption)
async def process_caption(message: Message, state: FSMContext):
    """
    Handler for processing photo caption.
    """
    data = await state.get_data()
    caption = None

    if message.text and not message.text.startswith('/'):
        caption = message.text.strip()
    elif message.text == "/skip":
        caption = None
    else:
        await message.reply("💭 <b>Расскажи о фото или пропусти</b>\n\n✨ Отправь текст описания или нажми /skip 💕", parse_mode="HTML")
        return

    # Add photo with or without caption
    if add_photo(
        file_id=data['file_id'],
        file_unique_id=data['file_unique_id'],
        filename=data.get('filename'),
        caption=caption,
        uploaded_by=message.from_user.id
    ):
        if caption:
            await message.reply("🌟 <b>Чудесная фотография добавлена!</b>\n\n💖 С таким красивым описанием она точно вдохновит участниц!\n\n✨ Спасибо за твою заботу! 💕", parse_mode="HTML")
        else:
            await message.reply("🌸 <b>Прекрасная фотография добавлена!</b>\n\n💕 Она будет радовать участниц клуба!\n\n✨ Спасибо за твою заботу! 💖", parse_mode="HTML")
    else:
        await message.reply("💔 <b>Ой, что-то пошло не так</b>\n\n❌ Не удалось добавить фотографию. Попробуй еще раз 💕", parse_mode="HTML")

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
        # Create a meaningful display name
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
        # Create a meaningful display name
        if caption and caption.strip():
            # Use caption if available (truncate if too long)
            display_name = caption.strip()[:35] + "..." if len(caption.strip()) > 35 else caption.strip()
        elif filename:
            # Use filename if available
            display_name = filename[:35] + "..." if len(filename) > 35 else filename
        else:
            # Use generic name with upload date
            upload_date = str(uploaded_at).split()[0]  # Get date part only
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
    else:
        await callback.message.edit_text("❌ Ошибка при удалении фотографии.")

    await callback.answer()


@router.message(Command("send_all"), IsAdmin())
async def cmd_send_all(message: Message, state: FSMContext, bot: Bot):
    await message.reply("💌 <b>Сообщение для всех участниц</b>\n\n✨ Напиши что-то теплое и вдохновляющее для нашего клуба! 💕\n\nВсе получат твое послание с любовью! 🌸", parse_mode="HTML")
    await state.set_state(SendAllStates.waiting_for_message)


@router.message(SendAllStates.waiting_for_message)
async def process_send_all(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    user_ids = get_all_user_ids_by_role('user')
    sent_count = 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            sent_count += 1
        except Exception:
            pass
    await message.reply(f"💌 <b>Сообщение отправлено!</b>\n\n✨ Дошло до {sent_count} из {len(user_ids)} участниц\n\n💕 Спасибо, что заботишься о нашем клубе! 🌸", parse_mode="HTML")
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
    else:
        await callback.message.edit_text("💔 <b>Ой, не получилось отменить событие</b>\n\n❌ Попробуй еще раз или обратись к администратору 💕", parse_mode="HTML")
    await callback.answer()
