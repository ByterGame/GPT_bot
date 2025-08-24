import asyncio
import aiohttp
from create_bot import bot
from config import MJ_KEY


POLL_INTERVAL = 10


async def send_prompt(prompt: str, user_id: int):
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
            data = await resp.json()
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return {"error": "Не удалось получить task_id", "data": data}
            return {"task_id": task_id}


async def poll_task(task_id: str, user_id: int):
    url = f"https://api.goapi.ai/api/v1/task/{task_id}"
    headers = {
        "X-API-KEY": MJ_KEY,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                status = data.get("data", {}).get("status")
                output = data.get("data", {}).get("output", {})

                if status in ("finished", "success", "completed"):
                    image_url = output.get("image_url")
                    if user_id and image_url:
                        await bot.send_photo(chat_id=user_id, photo=image_url)
                    return

                elif status in ("failed", "cancelled"):
                    await bot.send_message(chat_id=user_id, text="Не удалось сгенерировать изображение 😢")
                    return

            await asyncio.sleep(POLL_INTERVAL)


async def generate_image(prompt: str, user_id: int):
    result = await send_prompt(prompt, user_id)
    if "error" in result:
        await bot.send_message(chat_id=user_id, text="Ошибка при создании задачи.")
        return
    task_id = result["task_id"]
    await poll_task(task_id, user_id)
