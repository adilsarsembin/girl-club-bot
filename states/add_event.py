from aiogram.fsm.state import State, StatesGroup

class AddEventStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_theme = State()
    waiting_for_place = State()
