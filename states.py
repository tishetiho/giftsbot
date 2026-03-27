from aiogram.fsm.state import State, StatesGroup

class BuyGift(StatesGroup):
    waiting_for_gift_id = State()
    waiting_for_recipient = State()
    waiting_for_anonymous = State()
    waiting_for_comment = State()
    waiting_for_custom_comment = State()
    waiting_for_confirmation = State()

class AdminStates(StatesGroup):
    waiting_for_gift_add = State()
    waiting_for_gift_remove = State()