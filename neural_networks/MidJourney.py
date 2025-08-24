import requests
import time
from config import MJ_KEY


url = "https://api.goapi.ai/api/v1/task"
headers = {
    "X-API-KEY": MJ_KEY,
    "Content-Type": "application/json"
}
payload = {
    "model": "midjourney",
    "task_type": "imagine",
    "input": {
        "prompt": "realistic bmw drifting in desert",
        "aspect_ratio": "16:9",
        "process_mode": "",
        "skip_prompt_check": True,
        "bot_id": 0
    },
    "config": {
        "service_mode": "",
        "webhook_config": {
            "endpoint": "",
            "secret": ""
        }
    }
}

resp = requests.post(url, headers=headers, json=payload)
if resp:
    data = resp.json()
    print("Ответ imagine:", data)
    task_id = data.get("data", {}).get("task_id")
    if not task_id:
        raise Exception("Не удалось получить task_id")

    while True:
        time.sleep(5)
        fetch_resp = requests.get(f"{url}/{task_id}", headers=headers)
        status_data = fetch_resp.json().get("data", {})
        status = status_data.get("status")
        print("Статус задачи:", status)

        if status in ("finished", "success", "completed"):
            image_url = status_data.get("output", {}).get("image_url")
            print("Итоговая картинка:", image_url)
            break
else: 
    print(f"resp: {resp} is empty")


