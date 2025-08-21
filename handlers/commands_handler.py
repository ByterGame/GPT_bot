import logging
from datetime import datetime,timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from keyboards.all_inline_kb import set_mode_kb, pay_kb
from database.core import db


command_router = Router()
NEURAL_NETWORKS = ['set_gpt_4o_mini', 'set_gpt5_full', 'set_gpt5_vision', 'set_dalle']
PRICE_STARS = 100

@command_router.message(Command("mode"))
async def set_mode(message: Message):
    await message.answer("Выбери нейронку, с которой хочешь продолжить общение", reply_markup=set_mode_kb())


# @command_router.callback_query(F.data)
# async def test_call(call: CallbackQuery):
#     await call.answer()
#     await call.message.answer(call.data)


@command_router.callback_query(F.data.in_(NEURAL_NETWORKS))
async def set_mode(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    neural_index = NEURAL_NETWORKS.index(call.data)
    if neural_index > 0 and user.end_subscription_day.date() <= datetime.now().date(): # до индекса 0 включительно бесплатные нейронки
        await call.message.answer("Эта нейросеть доступна только по подписке!")
        return
    if neural_index == 2:
        await call.message.answer("Вы выбрали нейросеть gpt5-vision\nЭта нейросеть хорошо анализирует изображения, постарайтесь не тратить свои запросы на вопросы, которые не содержат изображение")
    if neural_index == 3:
        await call.message.answer("Вы выбрали DALL·E - нейросеть для генерации изображений. Одним сообщением опишите, какую картинку вы хотите получить и ожидайте (в скором времени добавим выбор размеров изображения и количества изображений)")
    await call.message.answer("Нейронка выбрана успешно!")
    user.current_neural_network = neural_index
    await db_repo.update_user(user)


@command_router.message(Command("pay"))
async def start_pay(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    text = ("В данный момент доступна оплата только звездами!\n"
            f"Стоимость месячной подписки {PRICE_STARS} telegram stars\n")
    if user.end_subscription_day.date() <= datetime.now().date():
        text += (f"Похоже сейчас у вас нет активной подписки, поэтому после оплаты вы получите подписку до {(datetime.now() + timedelta(days=30)).date()}\n")
    else:
        text += (f"Похоже у вас уже есть подписка, активная до {user.end_subscription_day.date()}\n"
                 f"Поэтому после оплаты ваша подписка просто продлится до {(user.end_subscription_day + timedelta(days=30)).date()}")
        
    await message.answer(text)
    await message.answer_invoice(  
        title="Месячная подписка",
        description="gpt 4o mini - безлимит\\ngpt 5 full - 50 запросов в день\\ngpt 5 vision - 25 запросов в день \\n DALL·E - 25 запросов в день",
        prices=[LabeledPrice(label="Месячная подписка", amount=PRICE_STARS)],  
        provider_token="",  
        payload=f"subscription_{message.from_user.id}_{datetime.now().timestamp()}",  
        currency="XTR", 
        parse_mode="MarkdownV2" 
    )

@command_router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    logging.info("Ожидание подтверждения")
    await pre_checkout_query.answer(ok=True)
    logging.info("Подтверждение отправлено")

@command_router.message(F.successful_payment)
async def successful_payment(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    
    if not user.end_subscription_day or user.end_subscription_day.date() < datetime.now().date():
        user.end_subscription_day = datetime.now() + timedelta(days=30)
    else:
        user.end_subscription_day += timedelta(days=30)
    
    await db_repo.update_user(user)
    await message.answer(f"Спасибо за оплату! Ваша подписка активна до {user.end_subscription_day.date()}")


@command_router.message(Command("clear_context"))
async def clear_context(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    user.context = None
    await db_repo.update_user(user)
    await message.answer("Контекст очищен!")


@command_router.message(Command("profile"))
async def let_profile_handler(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    text = ("Это ваш профиль.\n"
            "ID\n"
            f"{message.from_user.id}\n\n")
    if user.end_subscription_day.date() <= datetime.now().date():
        text += ("Сейчас у вас нет активной подписки\n"
                 "Для оформления подписки используйте команду /pay\n\n"
                 f"<b>Лимиты</b>:\ngpt 4o mini - осталось {user.gpt_4o_mini_requests}/30\n"
                 f"Обновление лимитов произойдет {(datetime.now() + timedelta(days=1)).date()} в 00:00 МСК")
    else:
        text += ("Сейчас у вас активна подписка\n\n"
                 f"<b>Лимиты</b>:\ngpt 4o mini - безлимитное использование\n"
                 f"gpt 5 full - осталось {user.gpt_5_requests}/50\n"
                 f"Обновление лимитов произойдет {(datetime.now() + timedelta(days=1)).date()} в 00:00 МСК")
        
    await message.answer(text)