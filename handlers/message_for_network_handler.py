import logging
import requests
import os
from aiogram import Router, F
from aiogram.types import Message
from neural_networks import gpt 
from neural_networks.MidJourney import generate_image
from database.core import db
from datetime import datetime
from create_bot import bot
from config import BOT_TOKEN, GOOGLE_API_KEY, CX_ID
from collections import defaultdict
from asyncio import sleep
from utils.all_utils import split_text_by_sentences
from database.models import User


general_router = Router()
NEURAL_NETWORKS = ['gpt-4o-mini', 'gpt-5', 'gpt-5-vision', 'DALL·E', 'Whisper', 'search with links', 'MidJorney']  # для понимания того, за какую нейронку отвечает индекс user.current_neural_network

album_buffer = defaultdict(list)

@general_router.message(F.media_group_id)
async def handle_album(message: Message):
    db_repo = await db.get_repository()
    album_id = message.media_group_id
    album_buffer[album_id].append(message)

    await sleep(1)
    messages = album_buffer.pop(album_id, None)
    if messages is None:
        logging.warning(f"Album {album_id} not found in buffer")
        return

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

    if len(reply) < 4000:
        await messages[0].answer(reply)
    else:
        chunks = split_text_by_sentences(reply)
        for chunk in chunks:
            await messages[0].answer(chunk)
    user.context = new_context
    await db_repo.update_user(user)


@general_router.message(F.voice | F.audio)
async def handle_audio_message(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)

    neural_index = user.current_neural_network

    if user.end_subscription_day.date() <= datetime.now().date() or user.whisper_requests < 1:
        await message.answer("Кажется у тебя нет подписки или твои запросы на сегодня уже закончились :(")
        return

    processing_msg = await message.answer("Преобразую аудио в текст...")

    file_id = message.voice.file_id if message.voice else message.audio.file_id

    file_info = await bot.get_file(file_id)

    local_path = f"./temp_{file_id}.ogg"
    await bot.download_file(file_info.file_path, local_path)

    transcript = gpt.transcribe_with_whisper(local_path)

    try:
        os.remove(local_path)
    except Exception as e:
        logging.warning(f"Не удалось удалить временный файл {local_path}: {e}")

    user.whisper_requests -= 1
    await db_repo.update_user(user)

    if neural_index != 4:
        fake_message = message.model_copy(update={"text": transcript})
        await simple_message_handler(fake_message)
        await processing_msg.delete()
        return

    if len(transcript) < 4000:
        await message.answer(transcript)
    else:
        from utils.all_utils import split_text_by_sentences
        chunks = split_text_by_sentences(transcript)
        for chunk in chunks:
            await message.answer(chunk)

    await processing_msg.delete()



@general_router.message()
async def simple_message_handler(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    if user.current_neural_network == 0:
        if user.gpt_4o_mini_requests < 1 and user.end_subscription_day.date() <= datetime.now().date():
            await message.answer("Кажется твои запросы на сегодня уже закончились:( "
                                    "Попробуй задать свой вопрос завтра, когда твои запросы восстановятся")
            return
        if message.photo:
            await message.answer("Для анализа изображений выбери gpt5 vision")
            return
        
        processing_msg = await message.answer("Думаю над твоим вопросом...")
        
        if user.end_subscription_day.date() <= datetime.now().date():
            user.gpt_4o_mini_requests -= 1
        reply, new_context = gpt.chat_with_gpt4o_mini(message.text, user.context if user.context else [])
        if len(reply) < 4000:
            await message.answer(reply)
        else:
            chunks = split_text_by_sentences(reply)
            for chunk in chunks:
                await message.answer(chunk)
        await processing_msg.delete()
        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 1:
        if user.end_subscription_day.date() <= datetime.now().date() or user.gpt_5_requests < 1:
            await message.answer("Кажется твои запросы на сегодня уже закончились:( "
                                    "Попробуй задать свой вопрос завтра, когда твои запросы восстановятся или используй другую нейросеть")
            return
        if message.photo:
            await message.answer("Для анализа изображений выбери gpt5 vision")
            return
        processing_msg = await message.answer("Думаю над твоим вопросом...")
        user.gpt_5_requests -= 1
        reply, new_context = gpt.chat_with_gpt5(message.text, user.context if user.context else [])
        if len(reply) < 4000:
            await message.answer(reply)
        else:
            chunks = split_text_by_sentences(reply)
            for chunk in chunks:
                await message.answer(chunk)
        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 2:
        if user.end_subscription_day.date() <= datetime.now().date() or user.gpt_5_vision_requests < 1:
            await message.answer("Кажется у тебя нет подписки или твои запросы на сегодня уже закончились:( \n"
                                    "Попробуй завтра или используй другую нейросеть")
            return

        processing_msg = await message.answer("Обрабатываю изображение...")

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

        if len(reply) < 4000:
            await message.answer(reply)
        else:
            chunks = split_text_by_sentences(reply)
            for chunk in chunks:
                await message.answer(chunk)
        await processing_msg.delete()
        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 3:
        if user.end_subscription_day.date() <= datetime.now().date() or user.dalle_requests < 1:
            await message.answer("Кажется у тебя нет подписки или твои запросы на сегодня закончились :(\n"
                                    "Попробуй завтра или используй другую нейросеть")
            return

        if message.photo:
            await message.answer("Для анализа изображений выбери gpt5 vision")
            return
        
        processing_msg = await message.answer("Генерирую изображение...") 
        
        user.dalle_requests -= 1

        prompt = message.caption if message.caption else message.text

        image_urls, new_context = gpt.generate_image_with_dalle(
            prompt=prompt,
            context=user.context if user.context else []
        )

        if image_urls:
            for url in image_urls:
                await message.answer_photo(url)
            await processing_msg.delete()
        else:
            await message.answer("Не удалось сгенерировать изображение :(")

        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 4:
        pass # Логика вынесена в отдельный хендлер
    elif user.current_neural_network == 5:
        await handle_search_with_links(message, user)
    elif user.current_neural_network == 6:
        if user.end_subscription_day.date() <= datetime.now().date() or user.midjourney_requests < 1:
            await message.answer("Кажется у тебя нет подписки или твои запросы на сегодня закончились :(\n"
                                 "Попробуй завтра или используй другую нейросеть")
            return

        if message.photo:
            await message.answer("Для анализа изображений выбери gpt5 vision")
            return
        
        
        proc_msg = await message.answer("⏳ Отправил запрос в MidJourney, жди картинку...")
        ans = await generate_image(message.text, message.from_user.id)

        # if "task_id" in ans:
        #     await message.answer(f"task_id: {ans["task_id"]}")
        #     await proc_msg.delete()
        # else:
        #     await message.answer(str(ans))
    else:
        logging.info(f"Текущая нейронка {user.current_neural_network}")


def web_search(query, max_results=3):

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CX_ID,
        "q": query,
        "num": max_results
    }

    r = requests.get(url, params=params)
    data = r.json()
    items = data.get("items", [])
    sources = []

    for item in items:
        sources.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "snippet": item.get("snippet")
        })

    return sources

async def handle_search_with_links(message: Message, user: User):
    db_repo = await db.get_repository()

    if user.end_subscription_day.date() <= datetime.now().date() or user.search_with_links_requests < 1:
        await message.answer("Кажется у тебя нет подписки или твои запросы на сегодня закончились :(")
        return

    query = message.text
    processing_msg = await message.answer("Ищу информацию в интернете...")

    sources = web_search(query)

    prompt = f"Используя эти источники, ответь на вопрос: {query}\n\n"
    for i, src in enumerate(sources, 1):
        prompt += f"{i}. {src['title']}: {src['url']}\n"

    prompt += "\nСделай краткий и понятный ответ с ссылками на источники."

    reply, new_context = gpt.chat_with_gpt4o_mini(
        message_text=prompt,
        context=user.context if user.context else []
    )

    if len(reply) < 4000:
        await message.answer(reply)
    else:
        from utils.all_utils import split_text_by_sentences
        chunks = split_text_by_sentences(reply)
        for chunk in chunks:
            await message.answer(chunk)

    user.context = new_context
    user.search_with_links_requests -= 1
    await db_repo.update_user(user)
    await processing_msg.delete()

