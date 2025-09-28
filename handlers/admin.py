from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.events import add_event
from database.quotes import add_quote
from database.users import get_all_user_ids_by_role
from filters import IsAdmin
from states.add_event import AddEventStates
from states.add_quote import AddQuoteStates
from states.send_all import SendAllStates

router = Router()


@router.message(Command("add_event"), IsAdmin())
async def cmd_add_event(message: Message, state: FSMContext):
    await message.reply("Enter event date (YYYY-MM-DD):")
    await state.set_state(AddEventStates.waiting_for_date)


@router.message(AddEventStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text.strip())
    await message.reply("Enter event theme:")
    await state.set_state(AddEventStates.waiting_for_theme)


@router.message(AddEventStates.waiting_for_theme)
async def process_theme(message: Message, state: FSMContext):
    await state.update_data(theme=message.text.strip())
    await message.reply("Enter event place:")
    await state.set_state(AddEventStates.waiting_for_place)


@router.message(AddEventStates.waiting_for_place)
async def process_place(message: Message, state: FSMContext):
    data = await state.get_data()
    date = data['date']
    theme = data['theme']
    place = message.text.strip()

    await message.reply(f"Event data collected: {date} - {theme} at {place}")
    place = message.text.strip()
    if add_event(date, theme, place):
        await message.reply(f"Event added: {date} - {theme} at {place}")
    else:
        await message.reply("Error adding event.")

    await state.clear()


@router.message(Command("add_quote"), IsAdmin())
async def cmd_add_quote(message: Message, state: FSMContext):
    await message.reply("Enter quote text:")
    await state.set_state(AddQuoteStates.waiting_for_quote)


@router.message(AddQuoteStates.waiting_for_quote)
async def process_quote(message: Message, state: FSMContext):
    text = message.text.strip()
    if add_quote(text):
        await message.reply("Quote added!")
    else:
        await message.reply("Error adding quote.")
    await state.clear()


@router.message(Command("send_all"), IsAdmin())
async def cmd_send_all(message: Message, state: FSMContext, bot: Bot):
    await message.reply("Enter message to send to all users:")
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
    await message.reply(f"Message sent to {sent_count}/{len(user_ids)} users.")
    await state.clear()
