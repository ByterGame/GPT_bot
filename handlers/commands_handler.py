from datetime import datetime,timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.all_inline_kb import set_mode_kb, pay_kb, delete_referer_kb 
from database.core import db
from create_bot import bot
from aiogram.fsm.context import FSMContext
from utils.encoding import encode_ref
from config import (DEFAULT_GPT_4O_LIMIT, PACKAGES, DALLE_PRICE, WHISPER_PRICE, GPT_5_TEXT_PRICE,
                    WEB_SEARCH_PRICE, GPT_4O_MINI_PRICE, GPT_5_VISION_PRICE, MIDJOURNEY_FAST_PRICE,
                    MIDJOURNEY_MIXED_PRICE, MIDJOURNEY_TURBO_PRICE, AUDIO_MARKUP,
                    TERMS_TEXT, PRIVACY_TEXT, SUPPORT_TEXT, REFUND_TEXT,
                    BONUS_TOKEN, DEFAULT_PROMPT, BOT_LINK_FOR_REFERAL)


command_router = Router()
NEURAL_NETWORKS = ['set_gpt_4o_mini', 'set_gpt5_full', 'set_gpt5_vision', 'set_dalle', 'set_whisper', 'set_web_search', 'set_midjorney']


@command_router.message(Command("mode"))
async def set_mode(message: Message):
    text = ("Выбери нейросеть с которой хочешь продолжить общение.\n"
            f"Любой запрос будет использовать твои токены, кроме бесплатных ежедневных запросов к gpt 4o mini ({DEFAULT_GPT_4O_LIMIT} запросов в день)\n\n"
            "<b>Текущие цены на запросы</b>:\n\n"
            f"- GPT 4o mini (после бесплатного периода): 1 запрос за {GPT_4O_MINI_PRICE} токен(ов)\n\n"
            f"- GPT 5 text: мощная нейросеть, воспринимает только текстовые сообщения. 1 запрос за {GPT_5_TEXT_PRICE} токен(ов)\n\n"
            f"- GPT 5 vision: мощная нейросеть, способная работать с изображениями. 1 запрос за {GPT_5_VISION_PRICE} токен(ов)\n\n"
            f"- DALLE: нейросеть для быстрой генерации изображений. 1 запрос за {DALLE_PRICE} токен(ов)\n\n"
            f"- Whisper: интсрумент для расшифровки аудио в текст. 1 запрос за {WHISPER_PRICE} токен(ов)\n\n"
            f"- Search with links: инструмент, позволяющий быстро найти нужную информацию в интеренете и предоставить источники. 1 запрос за {WEB_SEARCH_PRICE} токен(ов)\n\n"
            f"- MidJourney mixed: мощная нейросеть для генерации изображений. Параметр mixed предоставляет среднее качество генерации. 1 запрос за {MIDJOURNEY_MIXED_PRICE} токен(ов)\n\n"
            f"- MidJourney fast: мощная нейросеть для генерации изображений. Параметр fast предоставляет хорошее качество генерации. 1 запрос за {MIDJOURNEY_FAST_PRICE} токен(ов)\n\n"
            f"- MidJourney turbo: мощная нейросеть для генерации изображений. Параметр turbo предоставляет лучшее качество генерации. 1 запрос за {MIDJOURNEY_TURBO_PRICE} токен(ов)\n\n"
            f"- Вы также можете использовать аудио для общения. При использовании аудио любой запрос становится дороже на {AUDIO_MARKUP} токен(ов)")
    await message.answer(text, reply_markup=set_mode_kb())


@command_router.callback_query(F.data.in_(NEURAL_NETWORKS))
async def set_mode(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    neural_index = NEURAL_NETWORKS.index(call.data)
   
    if neural_index == 2:
        await call.message.answer("Вы выбрали нейросеть gpt5-vision\nЭта нейросеть хорошо анализирует изображения, постарайтесь не тратить свои запросы на вопросы, которые не содержат изображение")
    elif neural_index == 3:
        await call.message.answer("Вы выбрали DALLE - нейросеть для генерации изображений! Одним сообщением опишите, какую картинку вы хотите получить и ожидайте.")
    elif neural_index == 4:
        await call.message.answer("Вы выбрали whisper! Просто отправь мне телеграм аудио или файл, а я верну тебе его текстовую расшифровку!")
    elif neural_index == 5:
        await call.message.answer("Вы выбрали поиск с ссылками! Просто напишите свой запрос и ожидайте.")
    else:
        await call.message.answer("Нейросеть выбрана успешно!")
    user.current_neural_network = neural_index
    await db_repo.update_user(user)


@command_router.message(Command("pay"))
async def start_pay(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    text = ("В данный момент доступна оплата только звездами!\n\n"
            "<b>Для покупки представленны следующие пакеты</b>:\n\n")
    for package in PACKAGES:
        text += f"Пакет {package['name']} - {package['token_count']} токенов за {package['fiat_price']} рублей или {package['stars_price']} звезд!\n\n"
    text += f"В данный момент вам доступно {user.balance} токенов"
    if not user.with_bonus:
        text += f"\n\nВы можете получить бонусные {BONUS_TOKEN} токенов за подписку на наш канал!"
        await message.answer(text, reply_markup=pay_kb(with_bonus=True))
    else: 
        await message.answer(text, reply_markup=pay_kb(with_bonus=False))   


@command_router.message(Command("clear_context"))
async def clear_context(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
    await db_repo.update_user(user)
    await message.answer("Контекст очищен!")


@command_router.message(Command("referal"))
async def let_referal_info_command(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    if user.referal_id:
        referal = await bot.get_chat(user.referal_id)
        if referal:
            text = (f"Сейчас вы являетесь рефералом пользователя {'@' + referal.username if referal.username else referal.first_name}.\n\n"
                    "Вы не можете иметь своих рефералов пока сами являетесь рефералом.")
        else:
            text = ("Сейчас вы являетесь рефералом пользователя, о котором нет актуальной информации.\n\nВы не можете иметь своих рефералов пока сами являетесь рефералом.")
        await message.answer(text, reply_markup=delete_referer_kb())
    else:
        text = (f"Сейчас вы не являетесь чьм-либо рефералом, поэтому можете распространять свою ссылку для привлечения.\n\n"
                 "За каждое пополнение вашего реферала вы будете получать 10% бонусных токенов от размера пополения.\n\n"
                 f"Ваша персональная ссылка: {BOT_LINK_FOR_REFERAL}?start={encode_ref(message.from_user.id)}")
        referals = await db_repo.get_referals(user.id)
        if referals:
            text += ("\n\nВаши текущие рефералы:\n")
            unknown_referal = 0
            for referal in referals:
                referal_chat = await bot.get_chat(referal.id)
                if referal_chat:
                    text += (f"{'@' + referal_chat.username if referal_chat.username else referal_chat.first_name}\n")
                else:
                    unknown_referal += 1
            if unknown_referal:
                text += f"Также у вас есть {unknown_referal} реферал(ов), о которых сейчас нет информации"            
        await message.answer(text)


@command_router.callback_query(F.data=="referal_info")  
async def let_referal_info_call(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    if user.referal_id:
        referal = await bot.get_chat(user.referal_id)
        text = (f"Сейчас вы являетесь рефералом пользователя {'@' + referal.username if referal.username else referal.first_name}.\n\n"
                "Вы не можете иметь своих рефералов пока сами являетесь рефералом.")
        await call.message.answer(text, reply_markup=delete_referer_kb())
    else:
        text = (f"Сейчас вы не являетесь чьм-либо рефералом, поэтому можете распространять свою ссылку для привлечения.\n\n"
                 "За каждое пополнение вашего реферала вы будете получать 10% бонусных токенов от размера пополения.\n\n"
                 f"Ваша персональная ссылка: {BOT_LINK_FOR_REFERAL}?start={encode_ref(call.from_user.id)}")
        await call.message.answer(text) 


@command_router.callback_query(F.data=="delete_referer")
async def delete_referer(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    if user.referal_id:
        text = (f"Теперь вы не являетесь рефералом другого пользователя, поэтому можете получить собственных рефералом распространняя ссылку: {BOT_LINK_FOR_REFERAL}?start={call.from_user.id}") 
        await call.message.answer(text)
        user.referal_id = None
        await db_repo.update_user(user)
    else:
        await call.message.answer("Вы и так не являетесь чьим-либо рефералом") 
            

@command_router.message(Command("profile"))
async def let_profile_handler(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    text = ("Это ваш профиль.\n"
            "ID\n"
            f"{message.from_user.id}\n\n"
            f"<b>Ваш баланс</b>: {user.balance} токенов\n\n"
            f"Остаток бесплатных запросов к gpt 4o mini на сегодня - {user.gpt_4o_mini_requests}/{DEFAULT_GPT_4O_LIMIT}")
    
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

