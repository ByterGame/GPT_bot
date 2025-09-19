import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from neural_networks.MidJourney import send_prompt, poll_task
from database.core import db
from keyboards.all_inline_kb import mj_kb
from aiogram import Router, F
from aiogram.types import Message
from aiohttp import web
import logging
from create_bot import bot
from utils.download_photo import download_photo
from config import MIDJOURNEY_WAIT, LONG_PROCESSING_MJ, NOT_ENOUGH_TOKEN, VARIATIONS_MJ


midjourney_router = Router()


class VariationsState(StatesGroup):
    wait_prompt = State()


@midjourney_router.message(VariationsState.wait_prompt)
async def send_variation_request(message: Message, state: FSMContext):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    config = await db_repo.get_config()
    proc_msg = await message.answer(MIDJOURNEY_WAIT)
    data = await state.get_data()
    payload = {
        "model": "midjourney",
        "task_type": "variation",
        "input": {
            "prompt": message.text,
            "aspect_ratio": "16:9",
            "index": data['index'],
            "skip_prompt_check": False,
            "origin_task_id": data['origin_task_id']
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
        await db_repo.update_user(user)
    else:
        await message.answer("Произошла ошибка, попробуйте позже!")

    await state.clear()
    await proc_msg.delete()


@midjourney_router.callback_query(F.data.contains("variations"))
async def variations_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    config = await db_repo.get_config()
    if user.balance < config.Midjourney_mixed_price:
        await call.message.answer(NOT_ENOUGH_TOKEN)
        return
    data = call.data.split('_')
    origin_task_id = data[1]
    index = data[0][-1]
    data = {
        "index": index,
        "origin_task_id": origin_task_id
    }
    await state.set_data(data)
    await state.set_state(VariationsState.wait_prompt)
    await call.message.answer(VARIATIONS_MJ)
    

@midjourney_router.callback_query(F.data.contains("upscale"))
async def upscale_handler(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    config = await db_repo.get_config()
    if user.balance < config.Midjourney_mixed_price:
        await call.message.answer(NOT_ENOUGH_TOKEN)
        return
    proc_msg = await call.message.answer(MIDJOURNEY_WAIT)
    data = call.data.split('_')
    origin_task_id = data[1]
    index = data[0][-1]
    payload = {
        "model": "midjourney",
        "task_type": "upscale",
        "input": {
            "index": index,
            "origin_task_id": origin_task_id
        }
    }
    result = await send_prompt(payload)
    if "error" in result:
        logging.error(f"[generate_image] Ошибка при создании задачи: {result}")
        await call.message.answer("Ошибка при создании задачи")
        return 
    task_id = result["task_id"]
    image_url = await poll_task(task_id, call.from_user.id)

    if image_url:
        photo_file = await download_photo(image_url, task_id)
        if photo_file:
            await call.message.answer_photo(photo=photo_file)
        else:
            await call.message.answer((f"{LONG_PROCESSING_MJ}{image_url}"))
        user.balance -= config.Midjourney_mixed_price
        await db_repo.update_user(user)
    else:
        await call.message.answer("Произошла ошибка, попробуйте позже!")

    await proc_msg.delete()


mj_callback_router = Router()

pending_tasks = {}

@mj_callback_router.message(F.text)
async def handle_mj_callback(request: web.Request):
    try:
        data = await request.json()
        logging.info(f"Получен колбэк от Midjourney: {data}")
        
        task_id = data.get('job_id')
        status = data.get('status')
        image_url = data.get('image_url')
        error = data.get('error')
        
        if task_id in pending_tasks:
            user_id = pending_tasks[task_id]
            
            if status == 'completed' and image_url:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=image_url,
                    caption="Ваше изображение готово! 🎨"
                )
            elif status == 'failed' and error:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"Ошибка при генерации изображения: {error}"
                )
            
            del pending_tasks[task_id]
            
        return web.json_response({'status': 'ok'})
        
    except Exception as e:
        logging.error(f"Ошибка обработки колбэка: {e}")
        return web.json_response({'error': str(e)}, status=400)