import logging
from aiogram import Router, F
from aiogram.types import Message
from neural_networks import gpt 
from database.core import db
from datetime import datetime
from create_bot import bot
from config import BOT_TOKEN
from collections import defaultdict
from asyncio import sleep


general_router = Router()
NEURAL_NETWORKS = ['gpt-4o-mini', 'gpt-5', 'gpt-5-vision']  # для понимания того, за какую нейронку отвечает индекс user.current_neural_network

album_buffer = defaultdict(list)

@general_router.message(F.media_group_id)
async def handle_album(message: Message):
    db_repo = await db.get_repository()
    album_id = message.media_group_id
    album_buffer[album_id].append(message)

    await sleep(0.5)
    messages = album_buffer.pop(album_id)

    user = await db_repo.get_user(messages[0].from_user.id)

    if user.current_neural_network != 2:
        await messages[0].answer(f"Выбранная нейросеть не подходит для анализа изображений.\n\nСейчас вы используете {NEURAL_NETWORKS[user.current_neural_network]}")
        return

    if user.end_subscription_day.date() <= datetime.now().date() or user.gpt_5_vision_requests < 1:
        await messages[0].answer("Кажется у вас нет активной подписки на эту нейросеть или ваши запросы к ней закончились:(")
        return

    await messages[0].answer("Обрабатываю альбом...")

    image_urls = []
    for msg in messages:
        if msg.photo:
            photo = msg.photo[-1]
            file_info = await bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
            image_urls.append(url)

    user.gpt_5_vision_requests -= 1

    text = messages[0].caption or ""

    reply, new_context = gpt.chat_with_gpt5_vision(
        message_text=text,
        image_urls=image_urls,
        context=user.context if user.context else []
    )

    await messages[0].answer(reply)
    user.context = new_context
    await db_repo.update_user(user)


@general_router.message()
async def simple_message_handler(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    match user.current_neural_network:
        case 0:
            if user.gpt_4o_mini_requests < 1 and user.end_subscription_day.date() <= datetime.now().date():
                await message.answer("Кажется твои запросы на сегодня уже закончились:( "
                                     "Попробуй задать свой вопрос завтра, когда твои запросы восстановятся")
                return
            await message.answer("Думаю над твоим вопросом...")
            if user.end_subscription_day.date() <= datetime.now().date():
                user.gpt_4o_mini_requests -= 1
            reply, new_context = gpt.chat_with_gpt4o_mini(message.text, user.context if user.context else [])
            await message.answer(reply)
            user.context = new_context
            await db_repo.update_user(user)
        case 1:
            if user.end_subscription_day.date() <= datetime.now().date() or user.gpt_5_requests < 1:
                await message.answer("Кажется твои запросы на сегодня уже закончились:( "
                                     "Попробуй задать свой вопрос завтра, когда твои запросы восстановятся или используй другую нейросеть")
                return
            await message.answer("Думаю над твоим вопросом...")
            user.gpt_5_requests -= 1
            reply, new_context = gpt.chat_with_gpt5(message.text, user.context if user.context else [])
            await message.answer(reply)
            user.context = new_context
            await db_repo.update_user(user)
        case 2:
            if user.end_subscription_day.date() <= datetime.now().date() or user.gpt_5_vision_requests < 1:
                await message.answer("Кажется у тебя нет подписки или твои запросы на сегодня уже закончились:( \n"
                                     "Попробуй завтра или используй другую нейросеть")
                return

            await message.answer("Обрабатываю изображение...")

            image_url = []
            if message.photo:
                photo = message.photo[-1]
                file_info = await bot.get_file(photo.file_id)
                image_url.append(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

            user.gpt_5_vision_requests -= 1

            reply, new_context = gpt.chat_with_gpt5_vision(
                message_text=message.caption if message.caption else message.text,
                image_urls=image_url,
                context=user.context if user.context else []
            )

            await message.answer(reply)
            user.context = new_context
            await db_repo.update_user(user)
        case _:
            logging.info(f"Текущая нейронка {user.current_neural_network}")

