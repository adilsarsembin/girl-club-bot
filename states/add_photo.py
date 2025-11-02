from aiogram.fsm.state import State, StatesGroup

class AddPhotoStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_caption = State()
