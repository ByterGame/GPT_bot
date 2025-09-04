from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                           InlineKeyboardButton, InlineKeyboardMarkup)


def get_admin_kb(is_admin: bool):
    if is_admin:
        kb_list = [
            [KeyboardButton(text="Настроить пакеты")],
            [KeyboardButton(text="Добавить/удалить админа")],
            [KeyboardButton(text="Настроить бонусы")]
        ]
        return ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=False, is_persistent=True)
    return ReplyKeyboardRemove()


def configure_packages_kb():
    kb_list = [
        [InlineKeyboardButton(text="Изменить пакет", callback_data="change_package")],
        [InlineKeyboardButton(text="Удалить пакет", callback_data="del_package")],
        [InlineKeyboardButton(text="Добавить пакет", callback_data="add_package")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)


def confirm_delete_kb(index: int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Да, удалить", callback_data=f"confirm_delete_{index}")]])


def configure_admin_kb():
    kb_list = [
        [InlineKeyboardButton(text="Добавить админа", callback_data="add_admin")],
        [InlineKeyboardButton(text="Удалить админа", callback_data="delete_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)


def configure_bonus_kb():
    kb_list = [
        [InlineKeyboardButton(text="Изменить бонусный канал", callback_data="change_channel")],
        [InlineKeyboardButton(text="Изменить бонус за подписку", callback_data="change_bonus_for_sub")],
        [InlineKeyboardButton(text="Изменить бонус с рефералов", callback_data="change_referal_bonus")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)
