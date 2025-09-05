import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.core import db
from database.models import User
from config import START_MESSAGE
from utils.encoding import decode_ref
from keyboards.admin_keyboards import get_admin_kb


start_router = Router()


@start_router.message(CommandStart())
async def start_bot(message: Message): 
    args = message.text.split()
    
    await message.answer(START_MESSAGE)
    db_repo = await db.get_repository()
    
    new_user = User(id=message.from_user.id)
    if len(args) > 1:
        referer_id = decode_ref(args[1])
        if referer_id and referer_id != new_user.id: 
            await message.answer(f"Вы пришли по приглашению пользователя {referer_id}. Сейчас он назначен вашем рефералом.")
            new_user.referal_id = referer_id
    add_user = await db_repo.create_user(new_user)
    if add_user:
        logging.info(f"Добавлен новый пользователь id: {new_user.id}")
    else:
        logging.info(f"Пользователь с id {new_user.id} уже существует")
        user = await db_repo.get_user(message.from_user.id)
        if user.is_admin:
            await message.answer("Вы являетесь администратором, для взаимодействия с настройками бота воспользуйтесь клавиатурой ниже.", reply_markup=get_admin_kb())

