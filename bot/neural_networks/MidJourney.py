# import requests
# from config import DISCORD_CHANNEL_ID, DISCORD_SERVER_ID, DISCORD_TOKEN


# MJ_PROXY_URL = "http://localhost:8081/mj" 

# async def send_prompt(prompt: str):
#     headers = {
#         "Authorization": f"Bot {DISCORD_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     data = {
#         "prompt": prompt,
#         "channelId": DISCORD_CHANNEL_ID,
#         "guildId": DISCORD_SERVER_ID
#     }

#     try:
#         response = requests.post(f"{MJ_PROXY_URL}/submit/imagine", headers=headers, json=data, timeout=10)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         return {"error": f"Ошибка запроса: {e}"}

#     try:
#         return response.json()
#     except ValueError:
#         return {"error": f"Ответ сервера не JSON: {response.text}"}

import requests
from config import DISCORD_CHANNEL_ID, DISCORD_TOKEN, DISCORD_SERVER_ID

API_BASE = "https://discord.com/api/v10"

async def send_prompt(prompt: str):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "type": 2,
        "application_id": "936929561302675456",
        "guild_id": DISCORD_SERVER_ID,
        "channel_id": DISCORD_CHANNEL_ID,
        "data": {
            "version": "1118961510123847772",
            "id": "938956540159881230",
            "name": "imagine",
            "type": 1,
            "options": [
                {"type": 3, "name": "prompt", "value": prompt}
            ]
        }
    }

    r = requests.post(f"{API_BASE}/interactions", headers=headers, json=data)
    if r.status_code != 200:
        return {"error": f"{r.status_code}: {r.text}"}
    return str(r)
