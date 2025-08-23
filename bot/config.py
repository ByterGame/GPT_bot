from decouple import config

BOT_TOKEN = config('BOT_TOKEN')
WEBHOOK_HOST = config('WEBHOOK_HOST')
WEBHOOK_PATH = f'/webhook'
WEBHOOK_URL = f'https://{WEBHOOK_HOST}{WEBHOOK_PATH}'
PORT_BOT = config('PORT')
DATABASE_URL = config('DATABASE_URL')
SUPABASE_KEY = config('SUPABASE_KEY')
SUPABASE_URL = config('SUPABASE_URL')
OPENAI_API_KEY = config('OPENAI_API_KEY')
GOOGLE_API_KEY = config('GOOGLE_API_KEY')
CX_ID = config('CX_ID')
