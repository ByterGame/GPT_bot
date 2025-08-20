import logging
from datetime import datetime,timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, Update
from keyboards.all_inline_kb import set_mode_kb, pay_kb
from database.core import db


command_router = Router()
NEURAL_NETWORKS = ['set_gpt_4o_mini', 'set_gpt5_full']
PRICE_STARS = 25

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
        description="Продление подписки на 30 дней",
        prices=[LabeledPrice(label="Месячная подписка", amount=PRICE_STARS)],  
        provider_token="",  
        payload=f"subscription_{message.from_user.id}_{datetime.now().timestamp()}",  
        currency="XTR",  
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


@command_router.update()
async def catch_all(update: Update):
    logging.info(f"RAW UPDATE: {update}")
