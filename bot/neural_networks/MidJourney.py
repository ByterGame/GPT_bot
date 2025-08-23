import requests
from config import DISCORD_CHANNEL_ID, DISCORD_SERVER_ID, DISCORD_USER_TOKEN

MJ_PROXY_URL = "http://localhost:8081/mj"

async def send_prompt(prompt: str):
    headers = {
        "Authorization": f"Bearer {DISCORD_USER_TOKEN}", 
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "guildId": DISCORD_SERVER_ID,
        "channelId": DISCORD_CHANNEL_ID
    }

    try:
        response = requests.post(f"{MJ_PROXY_URL}/submit/imagine", headers=headers, json=data, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка запроса: {e}"}

    try:
        return response.json()
    except ValueError:
        return {"error": f"Ответ сервера не JSON: {response.text}"}
