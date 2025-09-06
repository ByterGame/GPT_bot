from datetime import datetime,timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from keyboards.all_inline_kb import set_mode_kb, pay_kb, delete_referer_kb, legal_document_kb
from database.core import db
from create_bot import bot
from aiogram.fsm.context import FSMContext
from utils.encoding import encode_ref
from config import (TERMS_TEXT, PRIVACY_TEXT, SUPPORT_TEXT, REFUND_TEXT, DEFAULT_PROMPT,
                    HELLO_MIDJOURENEY_FAST, HELLO_GPT_5_TEXT, HELLO_DALLE, HELLO_GPT_4O,
                    HELLO_GPT_5_VISION, HELLO_MIDJOURENEY_MIXED, HELLO_MIDJOURENEY_TURBO, HELLO_SEARCH_WITH_LINKS, HELLO_WHISPER,
                    CLEAR_CONTEXT, NEED_CANCEL, NO_NEED_CANCEL, LEGAL_DOCUMENT_TEXT)


command_router = Router()
NEURAL_NETWORKS = ['set_gpt_4o_mini', 'set_gpt5_text', 'set_gpt5_vision', 'set_dalle', 'set_whisper', 'set_web_search', 'set_midjorney_mixed', 'set_midjorney_fast', 'set_midjorney_turbo']


@command_router.message(Command("mode"))
async def set_mode(message: Message):
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    text = ("Выбери нейросеть с которой хочешь продолжить общение.\n"
            f"Любой запрос будет использовать твои токены, кроме бесплатных ежедневных запросов к gpt 4o mini ({config.default_4o_limit} запросов в день)\n\n"
            "<b>Текущие цены на запросы</b>:\n\n"
            f"- GPT 4o mini (после бесплатного периода): 1 запрос за {config.GPT_4o_mini_price} токен(ов)\n\n"
            f"- GPT 5 text: мощная нейросеть, воспринимает только текстовые сообщения. 1 запрос за {config.GPT_5_text_price} токен(ов)\n\n"
            f"- GPT 5 vision: мощная нейросеть, способная работать с изображениями. 1 запрос за {config.GPT_5_vision_price} токен(ов)\n\n"
            f"- DALLE: нейросеть для быстрой генерации изображений. 1 запрос за {config.Dalle_price} токен(ов)\n\n"
            f"- Whisper: интсрумент для расшифровки аудио в текст. 1 запрос за {config.Whisper_price} токен(ов)\n\n"
            f"- Search with links: инструмент, позволяющий быстро найти нужную информацию в интеренете и предоставить источники. 1 запрос за {config.search_with_links_price} токен(ов)\n\n"
            f"- MidJourney mixed: мощная нейросеть для генерации изображений. Параметр mixed предоставляет среднее качество генерации. 1 запрос за {config.Midjourney_mixed_price} токен(ов)\n\n"
            f"- MidJourney fast: мощная нейросеть для генерации изображений. Параметр fast предоставляет хорошее качество генерации. 1 запрос за {config.Midjourney_fast_price} токен(ов)\n\n"
            f"- MidJourney turbo: мощная нейросеть для генерации изображений. Параметр turbo предоставляет лучшее качество генерации. 1 запрос за {config.Midjourney_turbo_price} токен(ов)\n\n"
            f"- Вы также можете использовать аудио для общения. При использовании аудио любой запрос становится дороже на {config.Audio_markup} токен(ов)")
    await message.answer(text, reply_markup=set_mode_kb())


@command_router.callback_query(F.data.in_(NEURAL_NETWORKS))
async def set_mode(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    neural_index = NEURAL_NETWORKS.index(call.data)
    
    if neural_index == 0:
        await call.message.answer(HELLO_GPT_4O)
    elif neural_index == 1:
        await call.message.answer(HELLO_GPT_5_TEXT)
    elif neural_index == 2:
        await call.message.answer(HELLO_GPT_5_VISION)
    elif neural_index == 3:
        await call.message.answer(HELLO_DALLE)
    elif neural_index == 4:
        await call.message.answer(HELLO_WHISPER)
    elif neural_index == 5:
        await call.message.answer(HELLO_SEARCH_WITH_LINKS)
    elif neural_index == 6:
        await call.message.answer(HELLO_MIDJOURENEY_MIXED)
    elif neural_index == 7:
        await call.message.answer(HELLO_MIDJOURENEY_FAST)
    elif neural_index == 8:
        await call.message.answer(HELLO_MIDJOURENEY_TURBO)
    
    user.current_neural_network = neural_index
    await db_repo.update_user(user)


@command_router.message(Command("pay"))
async def start_pay(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    config = await db_repo.get_config()
    text = ("В данный момент доступна оплата только звездами!\n\n"
            "<b>Для покупки представленны следующие пакеты</b>:\n\n")
    for package in config.packages:
        text += f"{package['name']} - {package['fiat_price']}₽ ⭐️{package['stars_price']} = {package['token_count']} токенов.\n\n"
    text += f"В данный момент вам доступно {user.balance} токенов"
    if not user.with_bonus:
        text += f"\n\nВы можете получить бонусные {config.Bonus_token} токенов за подписку на наш канал!"
    await message.answer(text, reply_markup=pay_kb(with_bonus=(not user.with_bonus)))
    

@command_router.message(Command("clear_context"))
async def clear_context(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    user.context = [{"role": "system", "content": DEFAULT_PROMPT}]
    await db_repo.update_user(user)
    await message.answer(CLEAR_CONTEXT)


@command_router.message(Command("referal"))
async def let_referal_info_command(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    config = await db_repo.get_config()
    
    if user.referal_id:
        try:
            referal = await bot.get_chat(user.referal_id)
            text = (f"Сейчас вы являетесь рефералом пользователя {'@' + referal.username if referal.username else referal.first_name}.\n\n"
                    "Вы не можете иметь своих рефералов пока сами являетесь рефералом.")
        except TelegramBadRequest:
            text = ("Сейчас вы являетесь рефералом пользователя, о котором нет актуальной информации.\n\nВы не можете иметь своих рефералов пока сами являетесь рефералом.")
        await message.answer(text, reply_markup=delete_referer_kb())
    else:
        text = (f"Сейчас вы не являетесь чьм-либо рефералом, поэтому можете распространять свою ссылку для привлечения.\n\n"
                 f"За каждое пополнение вашего реферала вы будете получать {config.Referal_bonus}% бонусных токенов от размера пополения.\n\n"
                 f"Ваша персональная ссылка: {config.bot_link_for_referal}?start={encode_ref(message.from_user.id)}")
        
        referals = await db_repo.get_referals(user.id)
        if referals:
            text += "\n\nВаши текущие рефералы:\n"
            unknown_referal = 0
            known_referals = []
            
            for referal in referals:
                try:
                    referal_chat = await bot.get_chat(referal.id)
                    known_referals.append(f"{'@' + referal_chat.username if referal_chat.username else referal_chat.first_name}")
                except TelegramBadRequest:
                    unknown_referal += 1
            
            if known_referals:
                text += "\n".join(known_referals) + "\n"
            if unknown_referal:
                text += f"Также у вас есть {unknown_referal} реферал(ов), о которых сейчас нет информации"
        
        await message.answer(text)


@command_router.callback_query(F.data=="referal_info")  
async def let_referal_info_call(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    config = await db_repo.get_config()
    
    if user.referal_id:
        try:
            referal = await bot.get_chat(user.referal_id)
            text = (f"Сейчас вы являетесь рефералом пользователя {'@' + referal.username if referal.username else referal.first_name}.\n\n"
                    "Вы не можете иметь своих рефералов пока сами являетесь рефералом.")
        except TelegramBadRequest:
            text = ("Сейчас вы являетесь рефералом пользователя, о котором нет актуальной информации.\n\nВы не можете иметь своих рефералов пока сами являетесь рефералом.")
        await call.message.answer(text, reply_markup=delete_referer_kb())
    else:
        text = (f"Сейчас вы не являетесь чьм-либо рефералом, поэтому можете распространять свою ссылку для привлечения.\n\n"
                 f"За каждое пополнение вашего реферала вы будете получать {config.Referal_bonus}% бонусных токенов от размера пополения.\n\n"
                 f"Ваша персональная ссылка: {config.bot_link_for_referal}?start={encode_ref(call.from_user.id)}")
        
        referals = await db_repo.get_referals(user.id)
        if referals:
            text += "\n\nВаши текущие рефералы:\n"
            unknown_referal = 0
            known_referals = []
            
            for referal in referals:
                try:
                    referal_chat = await bot.get_chat(referal.id)
                    known_referals.append(f"{'@' + referal_chat.username if referal_chat.username else referal_chat.first_name}")
                except TelegramBadRequest:
                    unknown_referal += 1
            
            if known_referals:
                text += "\n".join(known_referals) + "\n"
            if unknown_referal:
                text += f"Также у вас есть {unknown_referal} реферал(ов), о которых сейчас нет информации"
        
        await call.message.answer(text)


@command_router.callback_query(F.data=="delete_referer")
async def delete_referer(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    config = await db_repo.get_config()
    if user.referal_id:
        text = (f"Теперь вы не являетесь рефералом другого пользователя, поэтому можете получить собственных рефералом распространняя ссылку: {config.bot_link_for_referal}?start={encode_ref(call.from_user.id)}\n"
                f"Вы будете получать {config.Referal_bonus}% токенов за каждое пополнение ваших рефералов") 
        await call.message.answer(text)
        user.referal_id = None
        await db_repo.update_user(user)
    else:
        await call.message.answer("Вы и так не являетесь чьим-либо рефералом") 
            

@command_router.message(Command("profile"))
async def let_profile_handler(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    config = await db_repo.get_config()
    text = ("Это ваш профиль.\n"
            "ID\n"
            f"{message.from_user.id}\n\n"
            f"<b>Ваш баланс</b>: {user.balance} токенов\n\n"
            f"Остаток бесплатных запросов к gpt 4o mini на сегодня - {user.gpt_4o_mini_requests}/{config.default_4o_limit}")
    
    await message.answer(text)


@command_router.message(Command("legal_documents"))
async def show_legal_documets(message: Message):
    await message.answer(LEGAL_DOCUMENT_TEXT, reply_markup=legal_document_kb())


@command_router.callback_query(F.data=="terms_document")
async def show_terms(call: CallbackQuery):
    await call.answer()
    await call.message.answer(TERMS_TEXT, parse_mode="HTML")


@command_router.callback_query(F.data=="privacy_document")
async def show_privacy(call: CallbackQuery):
    await call.answer()
    await call.message.answer(PRIVACY_TEXT, parse_mode="HTML")


@command_router.message(Command("support"))
async def show_support(message: Message):
    await message.answer(SUPPORT_TEXT, parse_mode="HTML")


@command_router.callback_query(F.data=="refund_document")
async def show_refund_policy(call: CallbackQuery):
    await call.answer()
    await call.message.answer(REFUND_TEXT, parse_mode="HTML")


@command_router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    if state.get_state():
        await state.clear()
        await message.answer(NEED_CANCEL)
    else:
        await message.answer(NO_NEED_CANCEL)

