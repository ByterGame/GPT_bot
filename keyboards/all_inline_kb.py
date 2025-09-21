from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
 

def set_mode_kb():
    kb_list = [
        [InlineKeyboardButton(text="gpt-4o mini", callback_data="set_gpt_4o_mini"), InlineKeyboardButton(text="gpt-5 text", callback_data="set_gpt5_text")],
        [InlineKeyboardButton(text="gpt-5 vision", callback_data="set_gpt5_vision"), InlineKeyboardButton(text="DALL·E", callback_data="set_dalle")],
        [InlineKeyboardButton(text="whisper", callback_data="set_whisper"), InlineKeyboardButton(text="Search with links", callback_data="set_web_search")],
        [InlineKeyboardButton(text="MidJorney mixed", callback_data="set_midjorney_mixed"), InlineKeyboardButton(text="MidJorney fast", callback_data="set_midjorney_fast")],
        [InlineKeyboardButton(text="MidJorney turbo", callback_data="set_midjorney_turbo")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def pay_kb(with_bonus: bool):
    kb_list = [[InlineKeyboardButton(text="Получить подписку в подарок", callback_data="pay_bonus_sub")]] if with_bonus else []

    
    kb_list.extend([
        [InlineKeyboardButton(text=f"купить за рубли", callback_data=f"buy_ruble")],
        [InlineKeyboardButton(text=f"купить за звезды", callback_data=f"buy_stars")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard


def fiat_pay_kb(url: str):
    kb_list = [[InlineKeyboardButton(text="Оплатить", url=url)]]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)


def select_pack_kb(packages: list, currency: str):
    kb_list = []
    for index, pack in enumerate(packages):
        kb_list.append([InlineKeyboardButton(text=f"{pack['name']}", callback_data=f"pack_{index}_{currency}")])
    return InlineKeyboardMarkup(inline_keyboard=kb_list)

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

def kb_with_bonus_channel(link: str):
    kb_list = [
        [InlineKeyboardButton(text="Канал, на который надо подписаться", url=f"https://{link}")],
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


def legal_document_kb():
    kb_list = [
        [InlineKeyboardButton(text="Пользовательское соглашение", callback_data="terms_document")],
        [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="privacy_document")],
        [InlineKeyboardButton(text="Политика возвратов", callback_data="refund_document")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)
