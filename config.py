from decouple import config

BOT_TOKEN = config('BOT_TOKEN')
WEBHOOK_HOST = config("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"
