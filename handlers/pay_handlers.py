import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from database.core import db
from keyboards.all_inline_kb import referal_kb, kb_with_bonus_channel, select_pack_kb
from create_bot import bot
from aiogram.exceptions import TelegramBadRequest
import aiohttp
import base64
import json
import hashlib
import hmac
import logging
from config import (REMINDER, SELECT_PACK_TEXT,
                    RB_PASSWORD1, RB_PASSWORD2,
                    RB_TEST_PASSWORD1, RB_TEST_PASSWORD2, 
                    RB_MERCHANT_LOGIN)


pay_router = Router()

async def create_invoice(user_id: int, package: dict):
    url = 'https://services.robokassa.ru/InvoiceServiceWebApi/api/CreateInvoice'

    header = {
        "typ": "JWT",
        "alg": "MD5"
    }
    encode_header = base64_encode(header)

    payload = {
            "MerchantLogin": RB_MERCHANT_LOGIN,
            "InvoiceType": "OneTime",
            "Culture": "ru",
            "InvId": None,
            "OutSum": str(package['fiat_price']),
            "Description": f"Покупка пакета {package['name']}",
            "MerchantComments": "test",
            "IsTest": 1,
            "UserFields": {
                "shp_user_id": str(user_id),
                "shp_package_name": package['name']
            },
            "InvoiceItems": [
                {
                "Name": f"Пакет {package['name']}",
                "Quantity": 1,
                "Cost": str(package['fiat_price']),
                "Tax": "vat20",
                "PaymentMethod": "full_payment",
                "PaymentObject": "commodity"
                }
            ]
        }
    encode_payload = base64_encode(payload)

    secret_string = f"{RB_MERCHANT_LOGIN}:{RB_TEST_PASSWORD1}"
    secret_key = base64.b64encode(secret_string.encode("utf-8"))

    signature = hmac.new(
        secret_key,
        f"{encode_header}.{encode_payload}".encode("utf-8"),
        hashlib.md5
    ).digest()

    encode_signature = base64_encode(signature)

    jwt_token = f"{encode_header}.{encode_payload}.{encode_signature}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            try:
                data = await response.json(content_type=None)
                logging.info("Ответ Робокассы: %s", data)
                if response.status == 200 and "InvoiceUrl" in data:
                    return data["InvoiceUrl"]
                else:
                    return None
            except Exception as e:
                text = await response.text()
                logging.error("Ошибка при запросе: %s | ответ: %s", e, text)
                return None

@pay_router.callback_query(F.data.startswith('buy_'))
async def select_pack(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    data = call.data.split("_") #["buy", currency]
    await call.message.answer(SELECT_PACK_TEXT, reply_markup=select_pack_kb(config.packages, data[1]))


@pay_router.callback_query(F.data.startswith('pack_'))
async def let_pay_message(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    data = call.data.split("_") # ["buy", index, currecy_type]
    package = config.packages[int(data[1])]
    if data[2] == "stars":
        await call.message.answer_invoice(
            title=f"Пакет {package['name']}",
            description="Детали в сообщении выше",
            prices=[LabeledPrice(label=f"Пакет {package['name']}", amount=package['stars_price'])],
            provider_token="",
            payload=f"{data[1]}_{call.from_user.id}",
            currency="XTR",
            start_parameter=f"index_pack{data[1]}_for_{call.from_user.id}"
        )
    else:
        resp = await create_invoice(call.from_user.id, package)
        if resp is not None:
            await call.message.answer(resp)
        else:
            await call.message.answer("Ошибка при создании платежа")

    await asyncio.sleep(240)
    user = await db_repo.get_user(call.from_user.id)
    if user.balance < 150: # цифра из головы, в будущем можно брать минимальный размер пакета минус 1 токен
        call.message.answer(REMINDER)


@pay_router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@pay_router.message(F.successful_payment)
async def successful_payment(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    config = await db_repo.get_config()
    payload = message.successful_payment.invoice_payload.split('_') # [index, user_id]
    package = config.packages[int(payload[0])]
    user.balance += package['token_count']
    text = (f"Спасибо за покупку!\n\nНа ваш баланс было начислено {package['token_count']} токенов. Сейчас у вас {user.balance} токенов!")
    if user.referal_id:
        referal = await db_repo.get_user(user.referal_id)
        referal.balance += (package['token_count'] * 0.1)
        text += (f"Мы также начислили бонус {int(package['token_count'] * config.Referal_bonus / 100)} токенов вашему рефереру.")
        await db_repo.update_user(referal)
        await message.answer(text, reply_markup=referal_kb())
    else:
        await message.answer(text)
    
    await db_repo.update_user(user)


@pay_router.callback_query(F.data == "pay_bonus_sub")
async def let_bonus_sub(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    user = await db_repo.get_user(call.from_user.id)
    config = await db_repo.get_config()
    if user.with_bonus:
        await call.message.answer("Кажется, вы уже получили бонус за подписку на канал.")
        return
    await call.message.answer(f"Ты можешь получить бонус {config.Bonus_token} токенов, при подписке на наш канал!", reply_markup=kb_with_bonus_channel(link=config.bonus_channel_link))
    
    
@pay_router.callback_query(F.data == "check_bonus_sub")
async def check_bonus_sub(call: CallbackQuery):
    await call.answer()
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    try:
        member = await bot.get_chat_member(
            chat_id=config.bonus_channel_id,
            user_id=call.from_user.id
        )
        
        valid_statuses = [
            'member', 'administrator', 'creator', 'restricted'
        ]
        
        if member.status in valid_statuses:
            await call.message.edit_text(
                f"✅ Отлично! Вы подписаны. Сейчас добавим к вашему балансу {config.Bonus_token} токенов!"
            )
            
            user = await db_repo.get_user(call.from_user.id)
            user.balance += config.Bonus_token
            user.with_bonus = True
            await db_repo.update_user(user)
            await call.message.answer(f"Ваш текущий баланс {user.balance}")
        else:
            await call.message.answer("Похоже вы не подписаны на канал или ваши настройки приватности не позволяют проверить это")
        
    except TelegramBadRequest as e:
        if "user not found" in str(e).lower() or "user not participant" in str(e).lower():
            await call.message.answer("Похоже вы не подписаны на канал или ваши настройки приватности не позволяют проверить это")
        raise e
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False   
    

def base64_encode(data):
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    elif isinstance(data, str):
        data = data.encode('utf-8')
    encoded = base64.urlsafe_b64encode(data).decode('utf-8')
    return encoded.rstrip('=')