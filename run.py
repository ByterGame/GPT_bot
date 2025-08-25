import asyncio
import pytz
from create_bot import bot, dp, logger, scheduler
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from database.core import db
from handlers.start_handler import start_router
from handlers.commands_handler import command_router
from handlers.message_for_network_handler import general_router
from aiohttp import web
from config import WEBHOOK_PATH, WEBHOOK_URL, PORT_BOT
from planned_activities.reset_limits import reset_limits
from neural_networks import MidJourney


async def on_startup():
    await set_commands()
    await bot.set_webhook(WEBHOOK_URL, 
                          drop_pending_updates=True,
                          allowed_updates=["message", "callback_query", "inline_query", 
                                           "edited_message", "pre_checkout_query", "successful_payment"])
    await db.connect()

async def main():
    await set_commands()

    dp.include_routers(start_router,
                       command_router,
                       general_router)
    
    dp.startup.register(on_startup)

    scheduler.start()

    scheduler.add_job(
        reset_limits,
        'cron',
        hour=7,
        minute=45,
        timezone=pytz.timezone('Europe/Moscow')
    )

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        handle_callback_query=True,
        handle_message=True,
        handle_edited_updates=True,
        handle_inline_query=True,
    )

    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(PORT_BOT)
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    
    try:
        await site.start()
        logger.info(f"Бот успешно запущен на порту {port}. URL: {WEBHOOK_URL}")
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()
        await bot.session.close()


async def set_commands():
    commands = [
        BotCommand(command="start", description="Запускает бота"),
        BotCommand(command="mode", description="Выбрать нейронку"),
        BotCommand(command="pay", description="Купить подписку"),
        BotCommand(command="profile", description="Профиль пользователя"),
        BotCommand(command="clear_context", description="очищает контекст"),
        BotCommand(command="terms", description="Пользовательское соглашение"),
        BotCommand(command="privacy", description="Политика конфиденциальности"),
        BotCommand(command="support", description="Поддержка"),
        BotCommand(command="refund", description="Политика возврата")
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
