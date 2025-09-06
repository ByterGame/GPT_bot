import logging
import requests
import os
from openai import BadRequestError
from aiogram import Router, F
from aiogram.types import Message
from neural_networks import gpt 
from neural_networks.MidJourney import send_prompt, poll_task
from database.core import db
from datetime import datetime
from create_bot import bot
from config import (BOT_TOKEN, GOOGLE_API_KEY, CX_ID, DEFAULT_PROMPT, UNSUITED_NEURAL, NOT_ENOUGH_TOKEN,
                    INTERIM_FOR_ALBUM, INACCESSIBLE_FILE, INTERIM_FOR_AUDIO, FREE_REQUESTS_RAN_OUT, 
                    FREE_REQUESTS_RAN_OUT_AND_NOT_ENOUGH_BALANCE, INTERIM_FOR_TEXT, INTERIM_FOR_IMAGE,
                    GENERATE_IMAGE, FAIL_GENERATE_IMAGE, MIDJOURNEY_WAIT, LONG_PROCESSING_MJ,
                    INSTRUCTION_MJ, INTERIM_FOR_SEARCH_LINKS
                    )
from collections import defaultdict
from asyncio import sleep
from utils.text_utils import safe_send_message
from database.models import User
from keyboards.all_inline_kb import mj_kb
from utils.download_photo import download_photo


general_router = Router()
NEURAL_NETWORKS = ['gpt-4o-mini', 'gpt-5', 'gpt-5-vision', 'DALL·E', 'Whisper', 'search with links', 'MidJorney']  # для понимания того, за какую нейронку отвечает индекс user.current_neural_network

album_buffer = defaultdict(list)

@general_router.message(F.media_group_id)
async def handle_album(message: Message):
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    album_id = message.media_group_id
    album_buffer[album_id].append(message)

    await sleep(1)
    messages = album_buffer.pop(album_id, None)
    if messages is None:
        logging.warning(f"Album {album_id} not found in buffer")
        return

    user = await db_repo.get_user(messages[0].from_user.id)

    if user.current_neural_network != 2:
        await messages[0].answer(f"{UNSUITED_NEURAL}{NEURAL_NETWORKS[user.current_neural_network]}")
        return

    if user.balance <= config.GPT_5_vision_price:
        await messages[0].answer(NOT_ENOUGH_TOKEN)
        return

    procces_msg: Message = await messages[0].answer(INTERIM_FOR_ALBUM)

    image_urls = []
    for msg in messages:
        if msg.photo:
            photo = msg.photo[-1]
            file_info = await bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
            image_urls.append(url)

    user.balance -= config.GPT_5_vision_price

    text = messages[0].caption or ""
    try:
        reply, new_context = gpt.chat_with_gpt5_vision(
            message_text=text,
            image_urls=image_urls,
            context=user.context if user.context else []
        )
    except BadRequestError as e: # я тут за все время видел только ошибку того, что юрл от картинки на сервере телеграм устарел, так что вся обработка сводится к очистки контекста
            await message.answer(INACCESSIBLE_FILE)
            user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
            await db_repo.update_user(user)
            return

    if len(reply) < 4000:
        await messages[0].answer(reply)
    else:
        await safe_send_message(message, reply)
    await procces_msg.delete()
    user.context = new_context
    await db_repo.update_user(user)


@general_router.message(F.voice | F.audio)
async def handle_audio_message(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    config = await db_repo.get_config()
    neural_index = user.current_neural_network

    if user.balance < config.Whisper_price:
        await message.answer(NOT_ENOUGH_TOKEN)
        return
    
    if user.current_neural_network != 4:
        price = await get_current_price(user.current_neural_network)
        if user.balance < config.Whisper_price + price:
            await message.answer(NOT_ENOUGH_TOKEN)
            return

    processing_msg = await message.answer(INTERIM_FOR_AUDIO)

    file_id = message.voice.file_id if message.voice else message.audio.file_id

    file_info = await bot.get_file(file_id)

    local_path = f"./temp_{file_id}.ogg"
    await bot.download_file(file_info.file_path, local_path)

    transcript = gpt.transcribe_with_whisper(local_path)

    try:
        os.remove(local_path)
    except Exception as e:
        logging.warning(f"Не удалось удалить временный файл {local_path}: {e}")

    

    if neural_index != 4:
        fake_message = message.model_copy(update={"text": transcript})
        await simple_message_handler(fake_message)
        await processing_msg.delete()
        return

    if len(transcript) < 4000:
        await message.answer(transcript)
    else:
        await safe_send_message(transcript)

    user.balance -= config.Whisper_price
    await db_repo.update_user(user)

    await processing_msg.delete()



@general_router.message()
async def simple_message_handler(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    config = await db_repo.get_config()
    if user.current_neural_network == 0:
        if user.gpt_4o_mini_requests < 1 and user.balance < config.GPT_4o_mini_price:
            await message.answer(FREE_REQUESTS_RAN_OUT_AND_NOT_ENOUGH_BALANCE)
            return
        if message.photo:
            await message.answer(UNSUITED_NEURAL)
            return
        
        processing_msg = await message.answer(INTERIM_FOR_TEXT)
        
        try:
            reply, new_context = gpt.chat_with_gpt4o_mini(message.text, user.context if user.context else [])
        except BadRequestError as e: # я тут за все время видел только ошибку того, что юрл от картинки на сервере телеграм устарел, так что вся обработка сводится к очистки контекста
            await message.answer(INACCESSIBLE_FILE)
            user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
            await db_repo.update_user(user)
            return
        await safe_send_message(message, reply)
        await processing_msg.delete()
        if user.gpt_4o_mini_requests > 0:
            user.gpt_4o_mini_requests -= 1
            if user.gpt_4o_mini_requests == 0:
                await message.answer(FREE_REQUESTS_RAN_OUT)
        else:
            user.balance -= config.GPT_4o_mini_price

        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 1:
        if user.balance < config.GPT_5_text_price:
            await message.answer(NOT_ENOUGH_TOKEN)
            return
        if message.photo:
            await message.answer(UNSUITED_NEURAL)
            return
        processing_msg = await message.answer(INTERIM_FOR_TEXT)
        try:
            reply, new_context = gpt.chat_with_gpt5(message.text, user.context if user.context else [])
        except BadRequestError as e: # я тут за все время видел только ошибку того, что юрл от картинки на сервере телеграм устарел, так что вся обработка сводится к очистки контекста
            await message.answer(INACCESSIBLE_FILE)
            user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
            await db_repo.update_user(user)
            return
        await safe_send_message(message, reply)
        user.balance -= config.GPT_5_text_price
        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 2:
        if user.balance < config.GPT_5_vision_price:
            await message.answer(NOT_ENOUGH_TOKEN)
            return

        processing_msg = await message.answer(INTERIM_FOR_IMAGE)

        image_url = []
        if message.photo:
            photo = message.photo[-1]
            file_info = await bot.get_file(photo.file_id)
            image_url.append(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

        try:
            reply, new_context = gpt.chat_with_gpt5_vision(
                message_text=message.caption if message.caption else message.text,
                image_urls=image_url,
                context=user.context if user.context else []
            )
        except BadRequestError as e: # я тут за все время видел только ошибку того, что юрл от картинки на сервере телеграм устарел, так что вся обработка сводится к очистки контекста
            await message.answer(INACCESSIBLE_FILE)
            user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
            await db_repo.update_user(user)
            return

        await safe_send_message(message, reply)
        await processing_msg.delete()
        user.balance -= config.GPT_5_vision_price
        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 3:
        if user.balance < config.Dalle_price:
            await message.answer(NOT_ENOUGH_TOKEN)
            return

        if message.photo:
            await message.answer(UNSUITED_NEURAL)
            return
        
        processing_msg = await message.answer(GENERATE_IMAGE) 

        prompt = message.caption if message.caption else message.text
        try:
            image_urls, new_context = gpt.generate_image_with_dalle(
                prompt=prompt,
                context=user.context if user.context else []
            )
        except BadRequestError as e: # я тут за все время видел только ошибку того, что юрл от картинки на сервере телеграм устарел, так что вся обработка сводится к очистки контекста
            await message.answer(INACCESSIBLE_FILE)
            user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
            await db_repo.update_user(user)
            return

        if image_urls:
            for url in image_urls:
                await message.answer_photo(url)
            await processing_msg.delete()
        else:
            await message.answer(FAIL_GENERATE_IMAGE)
        user.balance -= config.Dalle_price
        user.context = new_context
        await db_repo.update_user(user)
    elif user.current_neural_network == 4:
        pass # Логика вынесена в отдельный хендлер
    elif user.current_neural_network == 5:
        await handle_search_with_links(message, user)
    elif 6 <= user.current_neural_network <= 8:
        if user.current_neural_network == 6:
            price = config.Midjourney_mixed_price
            type = "mixed"
        if user.current_neural_network == 7:
            price = config.Midjourney_fast_price
            type = "fast"
        if user.current_neural_network == 8:
            price = config.Midjourney_turbo_price
            type = "turbo"
        if user.balance < config.Midjourney_mixed_price:
            await message.answer(NOT_ENOUGH_TOKEN)
            return

        if message.photo:
            await message.answer(UNSUITED_NEURAL)
            return
        
        
        proc_msg = await message.answer(MIDJOURNEY_WAIT)
        
        payload = {
            "model": "midjourney",
            "task_type": "imagine",
            "input": {
                "prompt": message.text,
                "aspect_ratio": "16:9",
                "process_mode": "mixed",
                "skip_prompt_check": False,
                "bot_id": 0
            }
        }
        result = await send_prompt(payload)
        if "error" in result:
            logging.error(f"[generate_image] Ошибка при создании задачи: {result}")
            await message.answer("Ошибка при создании задачи")
            return 
        task_id = result["task_id"]
        image_url = await poll_task(task_id, message.from_user.id)
        if image_url:
            user.balance -= config.Midjourney_mixed_price
            photo_file = await download_photo(image_url, task_id)
            if photo_file:
                await message.answer_photo(photo=photo_file, reply_markup=mj_kb(task_id))
            else:
                await message.answer((f"{LONG_PROCESSING_MJ}{image_url}"),
                                        reply_markup=mj_kb(task_id))
            text = (INSTRUCTION_MJ)
            await message.answer(text)
            await proc_msg.delete()
            await db_repo.update_user(user)
        else:
            await message.answer("Произошла ошибка, попробуйте позже!")
            await proc_msg.delete()
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
    config = await db_repo.get_config()
    if user.balance < config.search_with_links_price:
        await message.answer(NOT_ENOUGH_TOKEN)
        return

    query = message.text
    processing_msg = await message.answer(INTERIM_FOR_SEARCH_LINKS)

    sources = web_search(query)

    prompt = f"Используя эти источники, ответь на вопрос: {query}\n\n"
    for i, src in enumerate(sources, 1):
        prompt += f"{i}. {src['title']}: {src['url']}\n"

    prompt += "\nСделай краткий и понятный ответ с ссылками на источники."
    try:
        reply, new_context = gpt.chat_with_gpt4o_mini(
            message_text=prompt,
            context=user.context if user.context else []
        )
    except BadRequestError as e: # я тут за все время видел только ошибку того, что юрл от картинки на сервере телеграм устарел, так что вся обработка сводится к очистки контекста
            await message.answer(INACCESSIBLE_FILE)
            user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
            await db_repo.update_user(user)
            return

    await safe_send_message(message, reply)

    user.context = new_context
    user.balance -= config.search_with_links_price
    await db_repo.update_user(user)
    await processing_msg.delete()


async def get_current_price(neural_index: int):
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    if neural_index == 0:
        return config.GPT_4o_mini_price
    elif neural_index == 1:
        return config.GPT_5_text_price
    elif neural_index == 2:
        return config.GPT_5_vision_price
    elif neural_index == 3:
        return config.Dalle_price
    elif neural_index == 4:
        return config.Whisper_price
    elif neural_index == 5:
        return config.search_with_links_price
    elif neural_index == 6:
        return config.Midjourney_mixed_price