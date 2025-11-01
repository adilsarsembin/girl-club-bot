from datetime import date, timedelta, datetime

from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from database.events import add_event, deactivate_event, get_all_events
from database.quotes import add_quote
from database.users import get_all_user_ids_by_role
from filters import IsAdmin
from jobs import schedule_reminder
from states.add_event import AddEventStates
from states.add_quote import AddQuoteStates
from states.send_all import SendAllStates

router = Router()


@router.message(Command("add_event"), IsAdmin())
async def cmd_add_event(message: Message):
    markup = await SimpleCalendar().start_calendar()
    await message.reply("Выберите дату события:", reply_markup=markup)


@router.callback_query(SimpleCalendarCallback.filter())
async def process_date_selection(callback: CallbackQuery, state: FSMContext, callback_data: SimpleCalendarCallback):
    result, selected_date = await SimpleCalendar().process_selection(callback, callback_data)
    if result:
        await state.update_data(selected_date=selected_date.strftime('%Y-%m-%d'))
        await callback.message.edit_text(f"Дата: {selected_date.strftime('%Y-%m-%d')}\nВведите время (ЧЧ:ММ):")
        await state.set_state(AddEventStates.waiting_for_time)
    await callback.answer()


@router.message(StateFilter(AddEventStates.waiting_for_time))
async def process_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    data = await state.get_data()
    try:
        full_dt = datetime.strptime(f"{data['selected_date']} {time_str}", '%Y-%m-%d %H:%M')
        await state.update_data(full_datetime=full_dt.strftime('%Y-%m-%d %H:%M:%S'))
        await message.reply("Введите тему события:")
        await state.set_state(AddEventStates.waiting_for_theme)
    except ValueError:
        await message.reply("Неверное время. Используйте формат ЧЧ:ММ (например, 14:30):")


@router.message(StateFilter(AddEventStates.waiting_for_theme))
async def process_theme(message: Message, state: FSMContext):
    await state.update_data(theme=message.text.strip())
    await message.reply("Введите место проведения события:")
    await state.set_state(AddEventStates.waiting_for_place)


@router.message(StateFilter(AddEventStates.waiting_for_place))
async def process_place(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    place = message.text.strip()
    event_id = add_event(data['full_datetime'], data['theme'], place)
    if event_id:
        await schedule_reminder(bot, data['full_datetime'], event_id, data['theme'], place)
        await message.reply(f"Событие добавлено и напоминание запланировано: {data['full_datetime']} - {data['theme']} в {place}")
    else:
        await message.reply("Ошибка при добавлении события.")

    await state.clear()


@router.message(Command("add_quote"), IsAdmin())
async def cmd_add_quote(message: Message, state: FSMContext):
    await message.reply("Введите текст цитаты:")
    await state.set_state(AddQuoteStates.waiting_for_quote)


@router.message(AddQuoteStates.waiting_for_quote)
async def process_quote(message: Message, state: FSMContext):
    text = message.text.strip()
    if add_quote(text):
        await message.reply("Цитата добавлена!")
    else:
        await message.reply("Ошибка при добавлении цитаты.")
    await state.clear()


@router.message(Command("send_all"), IsAdmin())
async def cmd_send_all(message: Message, state: FSMContext, bot: Bot):
    await message.reply("Введите сообщение для отправки всем пользователям:")
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
    await message.reply(f"Сообщение отправлено {sent_count}/{len(user_ids)} пользователям.")
    await state.clear()


@router.message(Command("deactivate_event"), IsAdmin())
async def cmd_deactivate_event(message: Message):
    events = get_all_events()
    if not events:
        await message.reply("Нет активных событий.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for event_id, planned_at, theme, place in events:
        keyboard.inline_keyboard.append([InlineKeyboardButton(
            text=f"{planned_at} - {theme}", callback_data=f"deact:{event_id}"
        )])
    await message.reply("Выберите событие для деактивации:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("deact:"))
async def process_deactivate(callback: CallbackQuery):
    event_id = int(callback.data.split(":")[1])
    if deactivate_event(event_id):
        await callback.message.edit_text("Событие деактивировано.")
    else:
        await callback.message.edit_text("Ошибка.")
    await callback.answer()
