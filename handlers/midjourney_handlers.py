import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from neural_networks.MidJourney import send_prompt, poll_task
from database.core import db
from datetime import datetime
from keyboards.all_inline_kb import mj_kb


midjourney_router = Router()


class VariationsState(StatesGroup):
    wait_prompt = State()


@midjourney_router.message(VariationsState.wait_prompt)
async def send_variation_request(message: Message, state: FSMContext):
    proc_msg = await message.answer("⏳ Отправил запрос в MidJourney, жди картинку... \n(Приблизительное время ожидания 40 секунд)")
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
    image_url = await poll_task(task_id)

    if image_url:
        await message.answer(f"Ваше изображение готово, посмотреть и скачать его в оригинальном качестве вы можете по ссылке\n{image_url}",
                                reply_markup=mj_kb(task_id))
    else:
        await message.answer("Произошла ошибка, попробуйте позже!")

    await proc_msg.delete()


@midjourney_router.callback_query(F.data.contains("variations"))
async def variations_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    if user.midjourney_requests < 1 or user.end_subscription_day.date() <= datetime.now().date():
        await call.message.answer("Кажется у вас закончилась подписка или доступные запросы на сегодня.")
        return
    index, origin_task_id = call.data.split('-')
    index = index[-1]
    data = {
        index: index,
        origin_task_id: origin_task_id
    }
    await state.set_data(data)
    await state.set_state(VariationsState.wait_prompt)
    await call.message.answer(("Вы решили создать новые 4 вариации на основе стиля и композиции выбранного изображения или воспользуйтесь командой /cancel, если передумали.\n"
                                "Эта генерация потратит один из ваших запросов к MidJourney на сегодня"))
    

@midjourney_router.callback_query(F.data.contains("upscale"))
async def upscale_handler(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    if user.end_subscription_day.date() <= datetime.now().date():
        await call.message.answer("Кажется у вас закончилась подписка, вы всегда можете продлить ее использовав команду \pay")
        return
    proc_msg = await call.message.answer("⏳ Отправил запрос в MidJourney, жди картинку... \n(Приблизительное время ожидания 40 секунд)")
    index, origin_task_id = call.data.split('-')
    index = index[-1]
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
    image_url = await poll_task(task_id)

    if image_url:
        await call.message.answer(f"Ваше изображение готово, посмотреть и скачать его в оригинальном качестве вы можете по ссылке\n{image_url}")
    else:
        await call.message.answer("Произошла ошибка, попробуйте позже!")

    await proc_msg.delete()