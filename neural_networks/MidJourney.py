import aiohttp
from config import MJ_KEY, SECRET_TOKEN
from create_bot import bot
from aiohttp import web


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
        "config": {
            "service_mode": "",
            "webhook_config": {
                "endpoint": "https://GPT_Klon_ai.onrender.com/mj_webhook",
                "secret": SECRET_TOKEN
            }
        },
        "metadata": {
            "user_id": user_id
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            
            # if not resp:
            #     return {"error": f"resp: {resp} is empty"}

            data = await resp.json()

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return {"error": "Не удалось получить task_id", "data": data}

            return {"task_id": task_id}



async def mj_webhook(request: web.Request):
    body = await request.json()

    if body.get("secret") != SECRET_TOKEN:
        return web.json_response({"error": "Invalid secret"}, status=403)

    data = body.get("data", {})
    status = data.get("status")
    output = data.get("output", {})

    if status in ("finished", "success", "completed"):
        image_url = output.get("image_url")
        user_id = data.get("metadata", {}).get("user_id")

        if user_id and image_url:
            await bot.send_photo(chat_id=user_id, photo=image_url)

        return web.json_response({"message": "ok"})

    return web.json_response({"message": f"status={status}"})