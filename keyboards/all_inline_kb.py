from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def set_mode_kb():
    kb_list = [
        [InlineKeyboardButton(text="gpt-4o mini", callback_data="set_gpt_4o_mini"), InlineKeyboardButton(text="gpt-5 full", callback_data="set_gpt5_full")],
        [InlineKeyboardButton(text="gpt-5 vision", callback_data="set_gpt5_vision"), InlineKeyboardButton(text="DALL·E", callback_data="set_dalle")],
        [InlineKeyboardButton(text="whisper", callback_data="set_whisper")]
        # InlineKeyboardButton(text="MidJorney", callback_data="set_midjorney")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def pay_kb():
    kb_list = [
        InlineKeyboardButton(text="Купить подписку", callback_data="pay_sub")
    ]
