import requests
from config import DISCORD_CHANNEL_ID, DISCORD_SERVER_ID, DISCORD_TOKEN

MJ_PROXY_URL = "http://localhost:8081"

async def send_prompt(prompt: str):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "channelId": DISCORD_CHANNEL_ID,
        "guildId": DISCORD_SERVER_ID
    }

    response = requests.post(f"{MJ_PROXY_URL}/imagine", headers=headers, json=data)
    return response.json()
