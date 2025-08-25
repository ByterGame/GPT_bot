import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.core import db
from database.models import User
from config import START_MESSAGE


start_router = Router()


@start_router.message(CommandStart())
async def start_bot(message: Message):    
    await message.answer(START_MESSAGE)
    db_repo = await db.get_repository()
    
    new_user = User(id=message.from_user.id)
    add_user = await db_repo.create_user(new_user)
    if add_user:
        logging.info(f"Добавлен новый пользователь id: {new_user.id}")
    else:
        logging.info(f"Пользователь с id {new_user.id} уже существует")
