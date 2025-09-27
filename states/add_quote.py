from aiogram.fsm.state import State, StatesGroup

class AddQuoteStates(StatesGroup):
    waiting_for_quote = State()
