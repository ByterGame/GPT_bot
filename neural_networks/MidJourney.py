import asyncio
import aiohttp
import logging
from config import MJ_KEY
from create_bot import bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 15

pending_tasks = {}


async def send_prompt(payload: dict, user_id: int):
    url = "https://api.legnext.ai/api/v1/diffusion"
    headers = {
        "X-API-KEY": MJ_KEY,
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            try:
                data = await resp.json()
                logger.info(f"[send_prompt] Ответ API: {data}")
            except Exception as e:
                logger.error(f"[send_prompt] Ошибка при разборе JSON: {e}")
                return {"error": str(e)}

            task_id = data.get("job_id")
            pending_tasks[task_id] = user_id
            if not task_id:
                logger.error(f"[send_prompt] Не удалось получить task_id. Ответ: {data}")
                return {"error": "Не удалось получить task_id", "data": data}

            return {"task_id": task_id}


async def poll_task(task_id: str, user_id: int):
    url = f"https://api.goapi.ai/api/v1/task/{task_id}"
    headers = {
        "X-API-KEY": MJ_KEY,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        i = 0
        while True:
            if i % 4 == 0:
                await bot.send_message(chat_id=user_id, text = "Похоже, что генерация занимает немного больше времени... От нас не зависит скорость работы MidJorney, поэтому просим еще немного подождать")
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
           
                    if image_url:
                        try:
                            return image_url
                        except Exception as e:
                            logger.error(f"[poll_task] Ошибка при отправке фото: {e}")
                    return None

                elif status in ("failed", "cancelled"):
                    try:
                        return None
                    except Exception as e:
                        logger.error(f"[poll_task] Ошибка при отправке сообщения об ошибке: {e}")
                    return None

            logger.info(f"[poll_task] Задача еще не завершена, повтор через {POLL_INTERVAL} секунд...")
            await asyncio.sleep(POLL_INTERVAL)
            i += 1
        