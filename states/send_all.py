from aiogram.fsm.state import State, StatesGroup

class SendAllStates(StatesGroup):
    waiting_for_message = State()
