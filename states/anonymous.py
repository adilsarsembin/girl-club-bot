from aiogram.fsm.state import State, StatesGroup

class AnonymousStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()
