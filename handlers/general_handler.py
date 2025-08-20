from aiogram import Router
from aiogram.types import Message
from neural_networks import gpt 


general_router = Router()


@general_router.message()
async def simple_message_handler(message: Message):
    await message.answer(gpt.chat_with_gpt4o_mini(message.text))
