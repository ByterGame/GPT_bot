from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BONUS_CHANNEL_LINK, PACKAGES


def set_mode_kb():
    kb_list = [
        [InlineKeyboardButton(text="gpt-4o mini", callback_data="set_gpt_4o_mini"), InlineKeyboardButton(text="gpt-5 text", callback_data="set_gpt5_full")],
        [InlineKeyboardButton(text="gpt-5 vision", callback_data="set_gpt5_vision"), InlineKeyboardButton(text="DALL·E", callback_data="set_dalle")],
        [InlineKeyboardButton(text="whisper", callback_data="set_whisper"), InlineKeyboardButton(text="Search with links", callback_data="set_web_search")],
        [InlineKeyboardButton(text="MidJorney", callback_data="set_midjorney")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def pay_kb(with_bonus: bool):
    kb_list = [[InlineKeyboardButton(text="Получить подписку в подарок", callback_data="pay_bonus_sub")]] if with_bonus else []

    for index, package in enumerate(PACKAGES):
        kb_list.extend([
            [InlineKeyboardButton(text=f"купить {package['name']} за рубли", callback_data=f"buy_{index}_ruble")],
            [InlineKeyboardButton(text=f"купить {package['name']} за звезды", callback_data=f"buy_{index}_stars")]
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def referal_kb():
    kb_list = [
        [InlineKeyboardButton(text=f"Мой реферер", callback_data="referal_info")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)

def delete_referer_kb():
    kb_list = [
        [InlineKeyboardButton(text=f"Перестать быть рефералом", callback_data="delete_referer")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)

def kb_with_bonus_channel():
    kb_list = [
        [InlineKeyboardButton(text="Канал, на который надо подписаться", url=f"https://{BONUS_CHANNEL_LINK}")],
        [InlineKeyboardButton(text="Проверить подписку", callback_data="check_bonus_sub")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def mj_kb(task_id: str):
    kb_list = [
        [InlineKeyboardButton(text="V1", callback_data=f"variations1_{task_id}"), InlineKeyboardButton(text="V2", callback_data=f"variations2_{task_id}")],
        [InlineKeyboardButton(text="V3", callback_data=f"variations3_{task_id}"), InlineKeyboardButton(text="V4", callback_data=f"variations4_{task_id}")],
        [InlineKeyboardButton(text="U1", callback_data=f"upscale1_{task_id}"), InlineKeyboardButton(text="U2", callback_data=f"upscale2_{task_id}")],
        [InlineKeyboardButton(text="U3", callback_data=f"upscale3_{task_id}"), InlineKeyboardButton(text="U4", callback_data=f"upscale4_{task_id}")]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard
