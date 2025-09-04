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
MJ_KEY = config('MJ_KEY')
SECRET_TOKEN = config('SECRET_TOKEN')


DEFAULT_GPT_4O_LIMIT = 30
PACKAGES = [
    {"name": "Малый", "token_count": 500, "fiat_price": 199, "stars_price": 1},
    {"name": "Средний", "token_count": 2000, "fiat_price": 599, "stars_price": 700},
    {"name": "Большой", "token_count": 5000, "fiat_price": 1299, "stars_price": 1550}
]
GPT_4O_MINI_PRICE = 1
GPT_5_TEXT_PRICE = 5
GPT_5_VISION_PRICE = 10
DALLE_PRICE = 15
WHISPER_PRICE = 5
WEB_SEARCH_PRICE = 3
MIDJOURNEY_MIXED_PRICE = 15
MIDJOURNEY_FAST_PRICE = 45
MIDJOURNEY_TURBO_PRICE = 70
AUDIO_MARKUP = 2
BONUS_TOKEN = 50
BONUS_CHANNEL_LINK = 't.me/test_byter'
BOT_LINK_FOR_REFERAL = 'https://t.me/byter_test_bot'
BONUS_CHANNEL_ID = -1002888031843


TERMS_TEXT = ("📄 <b>Пользовательское соглашение</b>\n\n"
        "Здесь должно быть пользовательское соглашение\n\n"
        "• Условия предоставления услуг\n"
        "• Порядок оплаты и возвратов\n"
        "• Права и обязанности сторон\n"
        "• Срок действия соглашения\n\n"
        "<a href='https://example.com/'>По этой ссылке можно разместить полный текст</a>")

PRIVACY_TEXT = (
        "🔒 <b>Политика конфиденциальности</b>\n\n"
        "Здесь должна быть политика конфиденциальности\n\n"
        "• Какие данные мы собираем (хранятся собщения пользователя для контекста (можно очистить в любой момент), используем id пользователя в телеграм. Да вроде и все)\n"
        "• Как используем данные (id для идентификации оплаты, сообщения для контекста нейронкам)\n"
        "<a href='https://example.com/'>Полная версия на сайте</a>")

SUPPORT_TEXT = (
        "🛠 <b>Поддержка</b>\n\n"
        "По всем вопросам:\n"
        "• Telegram: @example\n"
        "• Время ответа: 24 часа\n\n"
        "Мы поможем решить любые проблемы!")

REFUND_TEXT = (
        "↩️ <b>Политика возвратов</b>\n\n"
        "Условия возврата средств:\n"
        "• Возврат в течение 30 дней\n"
        "• При технических неполадках\n"
        "• При неоказании услуг\n\n"
        "Для запроса возврата обращайтесь в поддержку")

START_MESSAGE = (
    "<b>Добро пожаловать!</b>\n\n"
    "Это бот для работы с актуальными моделями нейросетей в Telegram. Чтобы задать вопрос, просто напишите его.\n\n"
    "📋 <b>Доступные команды:</b>\n"
    "/start - Перезапуск бота\n"
    "/mode - Выбрать нейросеть\n"
    "/profile - Профиль пользователя\n"
    "/pay - Купить подписку\n"
    "/clear_context - Очистить контекст диалога\n"
    "/terms - Пользовательское соглашение\n"
    "/privacy - Политика конфиденциальности\n"
    "/support - Поддержка\n"
    "/refund - Политика возврата\n"
    "/referal - Информация о реферальной программе\n\n"
    "💡 <b>Просто напишите вопрос</b> - и нейросеть ответит вам!"
)

BONUS_TEXT = (f"Ты можешь получить бонус {BONUS_TOKEN} токенов, при подписке на наш канал!")

DEFAULT_PROMPT = ("Твои ответы будут пересланы в telegram обычным сообщением, поэтому следи, чтобы в твоих ответах использовались только "
                  "HTML теги без разметки. Длинна сообщений может быть любой, но постарайся, чтобы теги были закрыты до лимита по длинне сообщения в телеграм, у меня это 4000 символов.")
