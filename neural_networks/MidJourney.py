import asyncio
import aiohttp
import logging
import io
from create_bot import bot
from config import MJ_KEY
from aiogram.types import InputFile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 15


async def send_prompt(prompt: str, user_id: int):
    logger.info(f"[send_prompt] Отправка задачи для user_id={user_id} с промптом: {prompt}")
    url = "https://api.goapi.ai/api/v1/task"
    headers = {
        "X-API-KEY": MJ_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "midjourney",
        "task_type": "imagine",
        "input": {
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "process_mode": "mixed",
            "skip_prompt_check": True,
            "bot_id": 0
        },
        "metadata": {
            "user_id": user_id
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            try:
                data = await resp.json()
                logger.info(f"[send_prompt] Ответ API: {data}")
            except Exception as e:
                logger.error(f"[send_prompt] Ошибка при разборе JSON: {e}")
                return {"error": str(e)}

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                logger.error(f"[send_prompt] Не удалось получить task_id. Ответ: {data}")
                return {"error": "Не удалось получить task_id", "data": data}

            logger.info(f"[send_prompt] Получен task_id={task_id} для user_id={user_id}")
            return {"task_id": task_id}


async def poll_task(task_id: str, user_id: int):
    logger.info(f"[poll_task] Начало опроса задачи task_id={task_id} для user_id={user_id}")
    url = f"https://api.goapi.ai/api/v1/task/{task_id}"
    headers = {
        "X-API-KEY": MJ_KEY,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url, headers=headers) as resp:
                try:
                    data = await resp.json()
                    logger.info(f"[poll_task] Статус задачи: {data.get('data', {}).get('status')}")
                except Exception as e:
                    logger.error(f"[poll_task] Ошибка при разборе JSON: {e}")
                    await asyncio.sleep(POLL_INTERVAL)
                    continue

                status = data.get("data", {}).get("status")
                output = data.get("data", {}).get("output", {})

                if status in ("finished", "success", "completed"):
                    image_url = output.get("image_url")
           
                    if user_id and image_url:
                        logger.info(f"[poll_task] Задача завершена, отправка изображения пользователю {user_id}")
                        try:
                            await bot.send_message(user_id, f"Твое фото готово, забрать его в изначальном качестве можешь по этому адресу\n\n{image_url}")
                        except Exception as e:
                            logger.error(f"[poll_task] Ошибка при отправке фото: {e}")
                    return

                elif status in ("failed", "cancelled"):
                    logger.warning(f"[poll_task] Задача завершилась с ошибкой (status={status}) для user_id={user_id}")
                    try:
                        await bot.send_message(chat_id=user_id, text="Не удалось сгенерировать изображение 😢")
                    except Exception as e:
                        logger.error(f"[poll_task] Ошибка при отправке сообщения об ошибке: {e}")
                    return

            logger.info(f"[poll_task] Задача еще не завершена, повтор через {POLL_INTERVAL} секунд...")
            await asyncio.sleep(POLL_INTERVAL)


async def generate_image(prompt: str, user_id: int):
    logger.info(f"[generate_image] Генерация изображения для user_id={user_id} с промптом: {prompt}")
    result = await send_prompt(prompt, user_id)
    if "error" in result:
        logger.error(f"[generate_image] Ошибка при создании задачи: {result}")
        await bot.send_message(chat_id=user_id, text="Ошибка при создании задачи.")
        return
    task_id = result["task_id"]
    await poll_task(task_id, user_id)
