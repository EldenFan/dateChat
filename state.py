from aiogram.fsm.state import StatesGroup, State

class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_search_gender = State()
    waiting_for_goal = State()
    waiting_for_preferences = State()
    waiting_for_description = State()
    waiting_for_photo = State()
    waiting_for_location = State()
    adding_traits = State()
    waiting_for_selfcharacters = State()