from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BONUS_CHANNEL_LINK


def set_mode_kb():
    kb_list = [
        [InlineKeyboardButton(text="gpt-4o mini", callback_data="set_gpt_4o_mini"), InlineKeyboardButton(text="gpt-5 full", callback_data="set_gpt5_full")],
        [InlineKeyboardButton(text="gpt-5 vision", callback_data="set_gpt5_vision"), InlineKeyboardButton(text="DALL·E", callback_data="set_dalle")],
        [InlineKeyboardButton(text="whisper", callback_data="set_whisper"), InlineKeyboardButton(text="Search with links", callback_data="set_web_search")],
        [InlineKeyboardButton(text="MidJorney", callback_data="set_midjorney")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def pay_bonus_kb():
    kb_list = [
        InlineKeyboardButton(text="Получить подписку в подарок", callback_data="pay_bonus_sub")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def kb_with_bonus_channel():
    kb_list = [
        InlineKeyboardButton(text="Канал, на который надо подписаться", url=f"https://{BONUS_CHANNEL_LINK}"),
        InlineKeyboardButton(text="Проверить подписку", callback_data="check_bonus_sub")
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard
