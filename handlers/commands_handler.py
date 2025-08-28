import logging
from datetime import datetime,timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from keyboards.all_inline_kb import set_mode_kb, pay_bonus_kb, kb_with_bonus_channel
from database.core import db
from create_bot import bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from test import main
from config import (DEFAULT_GPT5_VISION_LIMIT, DEFAULT_GPT_4O_LIMIT, 
                    DEFAULT_GPT_5_LIMIT, DALLE_LIMIT, WHISPER_LIMIT, 
                    MIDJOURNEY_LIMIT, SEARCH_WITH_LINKS_LIMIT, 
                    PRICE_STARS, TERMS_TEXT, PRIVACY_TEXT, SUPPORT_TEXT, REFUND_TEXT,
                    BONUS_TEXT, BONUS_CHANNEL_ID, BONUS_PERIOD)


command_router = Router()
NEURAL_NETWORKS = ['set_gpt_4o_mini', 'set_gpt5_full', 'set_gpt5_vision', 'set_dalle', 'set_whisper', 'set_web_search', 'set_midjorney']


@command_router.message(Command("mode"))
async def set_mode(message: Message):
    await message.answer("Выбери нейросеть, с которой хочешь продолжить общение", reply_markup=set_mode_kb())


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
        await call.message.answer("Вы выбрали DALLE - нейросеть для генерации изображений! Одним сообщением опишите, какую картинку вы хотите получить и ожидайте.")
    if neural_index == 4:
        await call.message.answer("Вы выбрали whisper! Просто отправь мне телеграм аудио или файл, а я верну тебе его текстовую расшифровку!")
    if neural_index == 5:
        await call.message.answer("Вы выбрали поиск с ссылками! Просто напишите свой запрос и ожидайте.")
    await call.message.answer("Нейросеть выбрана успешно!")
    user.current_neural_network = neural_index
    await db_repo.update_user(user)


@command_router.message(Command("pay"))
async def start_pay(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    text = ("В данный момент доступна оплата только звездами!\n"
            f"Стоимость месячной подписки {PRICE_STARS} telegram stars\n"
            "Подписка предоставляет следующие преимущества:\n\n"
            "- gpt 4o mini - безлимит\n"
            f"- gpt 5 full - {DEFAULT_GPT_5_LIMIT} запросов в день\n"
            f"- gpt 5 vision - {DEFAULT_GPT5_VISION_LIMIT} запросов в день\n"
            f"- DALL·E - {DALLE_LIMIT} запросов в день\n"
            f"- Whisper - {WHISPER_LIMIT} запросов в день\n"
            f"- MidJourney - {MIDJOURNEY_LIMIT} запросов в день\n"
            f"- Search with links - {SEARCH_WITH_LINKS_LIMIT} запросов в день\n\n")
    if user.end_subscription_day.date() <= datetime.now().date():
        text += (f"Похоже сейчас у вас нет активной подписки, поэтому после оплаты вы получите подписку до {(datetime.now() + timedelta(days=30)).date()}\n")
    else:
        text += (f"Похоже у вас уже есть подписка, активная до {user.end_subscription_day.date()}\n"
                 f"Поэтому после оплаты ваша подписка просто продлится до {(user.end_subscription_day + timedelta(days=30)).date()}")
        
    await message.answer(text, reply_markup=pay_bonus_kb())
    await message.answer_invoice(
        title="Месячная подписка",
        description="Детали в сообщении выше",
        prices=[LabeledPrice(label="Месячная подписка", amount=PRICE_STARS)],
        provider_token="",
        payload=f"subscription_{message.from_user.id}_{datetime.now().timestamp()}",
        currency="XTR",
        start_parameter=f"subscription_{message.from_user.id}"
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


@command_router.callback_query(F.data == "pay_bonus_sub")
async def let_bonus_sub(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    if user.with_bonus:
        await call.message.answer("Кажется, вы уже получили бонус за подписку на канал.")
        return
    await call.message.answer(BONUS_TEXT, reply_markup=kb_with_bonus_channel())
    
@command_router.callback_query(F.data == "check_bonus_sub")
async def check_bonus_sub(call: CallbackQuery):
    await call.answer()
    try:
        member = await bot.get_chat_member(
            chat_id=BONUS_CHANNEL_ID,
            user_id=call.from_user.id
        )
        
        valid_statuses = [
            'member', 'administrator', 'creator', 'restricted'
        ]
        
        if member.status in valid_statuses:
            await call.message.edit_text(
                f"✅ Отлично! Вы подписаны. Сейчас добавим к вашей подписке {BONUS_PERIOD} дня!"
            )
            db_repo = await db.get_repository()
            user = await db_repo.get_user(call.from_user.id)
            user.end_subscription_day = (user.end_subscription_day + timedelta(days=int(BONUS_PERIOD)) 
                                         if user.end_subscription_day.date() > datetime.now().date() 
                                         else datetime.now() + timedelta(days=int(BONUS_PERIOD)))
            user.with_bonus = True
            await db_repo.update_user(user)
            await call.message.answer(f"Ваша текущая подписка теперь действительна до {user.end_subscription_day.date()}")
        else:
            await call.message.answer("Похоже вы не подписаны на канал или ваши настройки приватности не позволяют проверить это")
        
    except TelegramBadRequest as e:
        if "user not found" in str(e).lower() or "user not participant" in str(e).lower():
            await call.message.answer("Похоже вы не подписаны на канал или ваши настройки приватности не позволяют проверить это")
        raise e
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False      


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
                 f"<b>Лимиты</b>:\n- gpt 4o mini - осталось {user.gpt_4o_mini_requests}/{DEFAULT_GPT_4O_LIMIT}\n"
                 f"Обновление лимитов произойдет {(datetime.now() + timedelta(days=1)).date()} в 00:00 МСК")
    else:
        text += ("Сейчас у вас активна подписка\n\n"
                 f"<b>Лимиты</b>:\n- gpt 4o mini - безлимитное использование\n"
                 f"- gpt 5 full - осталось {user.gpt_5_requests}/{DEFAULT_GPT_5_LIMIT}\n"
                 f"- gpt 5 vision - осталось {user.gpt_5_vision_requests}/{DEFAULT_GPT5_VISION_LIMIT}\n"
                 f"- DALL·E - осталось {user.dalle_requests}/{DALLE_LIMIT}\n"
                 f"- Whisper - осталось {user.whisper_requests}/{WHISPER_LIMIT}\n"
                 f"- MidJourney - осталось {user.midjourney_requests}/{MIDJOURNEY_LIMIT}\n"
                 f"- Search with links - осталось {user.search_with_links_requests}/{SEARCH_WITH_LINKS_LIMIT}.\n\n"
                 f"Обновление лимитов произойдет {(datetime.now() + timedelta(days=1)).date()} в 00:00 МСК")
        
    await message.answer(text)


@command_router.message(Command("terms"))
async def show_terms(message: Message):
    await message.answer(TERMS_TEXT, parse_mode="HTML")


@command_router.message(Command("privacy"))
async def show_privacy(message: Message):
    await message.answer(PRIVACY_TEXT, parse_mode="HTML")


@command_router.message(Command("support"))
async def show_support(message: Message):
    await message.answer(SUPPORT_TEXT, parse_mode="HTML")


@command_router.message(Command("refund"))
async def show_refund_policy(message: Message):
    await message.answer(REFUND_TEXT, parse_mode="HTML")


@command_router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    if state.get_state():
        await state.clear()
        await message.answer("Хорошо, скажи, если что-то понадобится!")
    else:
        await message.answer("Сейчас я ничего не ждал от тебя, можешь спокойно продолжать использование:)")

@command_router.message(Command("test"))
async def test(message: Message):
    await main("https://img.theapi.app/mj/17f89940-fb9e-4ff1-a391-058b80c77fd6.png", 1335226579)
