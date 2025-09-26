import os

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from filters import IsAdmin
from states.add_event import AddEventStates

from dotenv import load_dotenv

load_dotenv()
ADMIN_IDS_STR = os.getenv("ADMIN_IDS")
ADMIN_IDS = {int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',')}

router = Router()


@router.message(Command("admin"), IsAdmin())
async def admin_panel(message: types.Message):
    """
    Handler for the /admin command. Only accessible to users in ADMIN_IDS.
    """
    await message.reply("Welcome to the Admin Panel! 🛠️\nHere you can manage the bot's content.")


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
    # TODO: Integrate DB save here next step

    await state.clear()
