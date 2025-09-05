from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.core import db
from database.models import User
from keyboards.admin_keyboards import configure_packages_kb, confirm_delete_kb, configure_admin_kb, configure_bonus_kb
from create_bot import bot


class AdminStates(StatesGroup):
    select_package_to_change = State()
    change_package = State()
    select_package_to_delete = State()
    add_package = State()
    add_admin = State()
    delete_admin = State()
    change_channel = State()
    change_bonus_for_sub = State()
    change_referal_bonus = State()


admin_router = Router()


async def is_admin(message: Message):
    db_repo = await db.get_repository()
    user = await db_repo.get_user(message.from_user.id)
    return user.is_admin


@admin_router.message(F.text=="Настроить пакеты", is_admin)
async def configure_packages(message: Message):
    text = ("Сейчас доступны следующие пакеты:\n")
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    for index, package in enumerate(config.packages):
        text += (f"{index + 1}) {package['name']} - {package['token_count']} токенов за {package['fiat_price']} рублей или {package['stars_price']} звезд\n\n")
    await message.answer(text, reply_markup=configure_packages_kb())


@admin_router.callback_query(F.data=="change_package")
async def change_package(call: CallbackQuery, state: FSMContext):
    await call.answer()
    text = ("Напишите номер пакета, который хотите изменить из списка пакетов выше (одно число)\n"
            "ЭТО НОМЕР -> 1) Малый - ....\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.select_package_to_change)


@admin_router.message(AdminStates.select_package_to_change, is_admin)
async def select_package_to_change(message: Message, state: FSMContext):
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        index = int(message.text) - 1
        package = config.packages[index]
        text = (f"Вы хотите изменить пакет \"{package['name']}\"? Если это так, то в следующем сообщении укажите следующие данные в следующем формате\n"
                f"&ИМЯ ПАКЕТА& - &КОЛ-ВО ТОКЕНОВ& - &ЦЕНА В РУБЛЯХ& - &ЦЕНА В ЗВЕЗДАХ&\n\n"
                f"<b>Пример:</b> \"Малый - 500 - 250 - 350\". Тут я изменил цену пакета."
                f"Я указал, что выбранный пакет отныне называется \"Малый\", в нем 500 токенов за 250 рублей или 350 звезд\n"
                "Для отмены используй команду /cancel")
        await message.answer(text)
        await state.set_data({"index": index})
        await state.set_state(AdminStates.change_package)
    except Exception as e:
        await message.answer(f"ошибка {e}\n\nВероятно вы ввели не одно число или такого номера нет в списке пакетов")


@admin_router.message(AdminStates.change_package, is_admin)
async def change_package(message: Message, state: FSMContext):
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        data = await state.get_data()
        new_package = message.text.split("-")  # [Имя, токены, цена рубли, цена звезды]
        config.packages[data['index']]['name'] = new_package[0].strip()
        config.packages[data['index']]['token_count'] = int(new_package[1])
        config.packages[data['index']]['fiat_price'] = int(new_package[2])
        config.packages[data['index']]['stars_price'] = int(new_package[3])
        await message.answer("Параметры пакета успешно изменены!")
        await state.clear()
        await db_repo.update_config(config)
    except Exception as e:
        await message.answer(f"ошибка {e}.\n\nПопробуйте снова")


@admin_router.callback_query(F.data=="del_package")
async def delete_package(call: CallbackQuery, state: FSMContext):
    await call.answer()
    text = ("Вы хотите удалить существующий пакет? Для удаления отправте мне номер пакета из списка. (одно число)\n"
            "ЭТО НОМЕР -& 1) Малый - ....\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.select_package_to_delete)


@admin_router.message(AdminStates.select_package_to_delete, is_admin)
async def select_package_to_delete(message: Message):
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        index = int(message.text) - 1
        package = config.packages[index]
        text = (f"Вы хотите удалить пакет \"{package['name']}\"? Если это так, то нажмите на кнопку ниже\n"
                "Для отмены используй команду /cancel")
        await message.answer(text, reply_markup=confirm_delete_kb(index))
    except Exception as e:
        await message.answer(f"ошибка {e}\n\nВероятно вы ввели не одно число или такого номера нет в списке пакетов")


@admin_router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        index = int(call.data.split('_')[2])
        del config.packages[index]
        await call.message.answer(f'Пакет "{config.packages[index]['name']}" был удален')
        await state.clear()
        await db_repo.update_config(config)
    except Exception as e:
        await call.message.answer(f"ошибка {e}.\n\nПопробуйте снова")


@admin_router.callback_query(F.data=="add_package")
async def info_about_add_package(call: CallbackQuery, state: FSMContext):
    await call.answer()
    text = (f"Вы хотите добавить пакет? Если это так, то в следующем сообщении укажите следующие данные в следующем формате\n"
            f"&ИМЯ ПАКЕТА& - &КОЛ-ВО ТОКЕНОВ& - &ЦЕНА В РУБЛЯХ& - &ЦЕНА В ЗВЕЗДАХ& - &ЖЕЛАЕМЫЙ НОМЕР В СПИСКЕ&\n\n"
            f"<b>Пример:</b> \"Малый - 500 - 250 - 350 - 2\".\n"
            f"Я указал, что хочу добавить пакет \"Малый\", в нем 500 токенов за 250 рублей или 350 звезд и занять он должен второй номер в спике (все остальные пакеты начиная со второго просто прибавят в номере)\n"
            f"Вы также можете не указывать номер и отправить текст вида \"Малый - 500 - 250 - 350\", в таком случае пакет поместится в конец списка\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.add_package)


@admin_router.message(AdminStates.add_package, is_admin)
async def add_package(message: Message, state: FSMContext):
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        data: list[str] = message.text.split('-')  # [Имя, токены, цена рубли, цена звезды, номер в списке(optional)]
        text = (f'Был добавлен пакет {data[0].strip()}, количество токенов - {data[1].strip()} за {data[2].strip()} рублей или {data[3].strip()} звезд')
        if len(data) == 5: # Есть желаемый номер
            text += f" под номером {data[4].strip()}"
            new_package = {
                "name": data[0].strip(),
                "token_count": int(data[1]),
                "fiat_price": int(data[2]),
                "stars_price": int(data[3])
            }
            config.packages.insert(int(data[4]) - 1, new_package)
        else:
            config.packages.append({"name": data[0].strip(), "token_count": int(data[1]), "fiat_price": int(data[2]), "stars_price": int(data[3])})

        await message.answer(text)
        await state.clear()
        await db_repo.update_config(config)
    except Exception as e:
        await message.answer(f"ошибка {e}.\n\nПопробуйте снова")


@admin_router.message(F.text=="Добавить/удалить админа", is_admin)
async def configure_admin(message: Message):
    text = ("Список текущих администраторов:\n\n")
    db_repo = await db.get_repository()
    admins_id = await db_repo.get_admins()
    for id in admins_id:
        chat = await bot.get_chat(id)
        if chat:
            text += f"id: {id}, tag/name: {'@' + chat.username if chat.username else chat.first_name}\n"
        else:
            text += f"id: {id}. Бот не может получить другие данные этого пользователя, возможно у него не начат чат с ботом.\n"
    await message.answer(text, reply_markup=configure_admin_kb())


@admin_router.callback_query(F.data=="add_admin")
async def info_about_add_admin(call: CallbackQuery, state: FSMContext):
    await call.answer()
    text = ("Чтобы добавить администратора укажите в следующем сообщении его telegram id (набор цифр без пробелов)\n"
            "<b>Например:</b> 1335226579\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.add_admin)


@admin_router.message(AdminStates.add_admin, is_admin)
async def add_admin(message: Message, state: FSMContext):
    try:
        id = int(message.text.replace(' ', ''))
        db_repo = await db.get_repository()
        user = await db_repo.get_user(id)
        if user: 
            user.is_admin = True
            await db_repo.update_user(user)
        else:
            user = User(id=id, is_admin=True)
            await db_repo.create_user(user)
        await message.answer("Администратор был добавлен!")
        await state.clear()
    except Exception as e:
        await message.answer(f"ошибка {e}\n\nУбедитесь, что вы вводите одно число без пробелов")


@admin_router.callback_query(F.data=="delete_admin")
async def info_about_delete_user(call: CallbackQuery, state: FSMContext):
    await call.answer()
    text = ("Для удаления админа отправь мне его id из списка админов в следующем сообщении\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.delete_admin)


@admin_router.message(AdminStates.delete_admin, is_admin)
async def delete_admin(message: Message, state: FSMContext):
    try:
        id = int(message.text.replace(' ', ''))
        db_repo = await db.get_repository()
        user = await db_repo.get_user(id)
        if user: 
            user.is_admin = False
            await db_repo.update_user(user)
        else:
            await message.answer("Такого пользователя нет в базе данных. Проверьте id и попробуйте отправить мне его еще раз в следующем сообщении!\n"
                                 "Для отмены используй команду /cancel")
            return
        await message.answer("Администратор был удален!")
        await state.clear()
    except Exception as e:
        await message.answer(f"ошибка {e}\n\nУбедитесь, что вы вводите одно число без пробелов")


@admin_router.message(F.text=="Настроить бонусы", is_admin)
async def configure_bonus(message: Message):
    await message.answer("Вы можете изменить канал, за который хотите выдавать бонус или изменить количество бонусных токенов.", reply_markup=configure_bonus_kb())


@admin_router.callback_query(F.data=="change_channel")
async def info_about_change_channel(call: CallbackQuery, state: FSMContext):
    await call.answer()
    text = ("Для смены бонусного канала отправь в следующем сообщении ссылку на канал и его id без пробелов в следующем формате\n\n"
            "&ССЫЛКА& - &TELEGRAM ID& - &ФЛАГ СБРОСА&\n"
            "ФЛАГ СБРОСА - отвечает за то, нужно ли сбросить предыдущие бонусы, чтобы все пользователи снова могли получить бонус (0 - оставить старые бонусы, 1 - сбросить бонусы, чтобы можно было получить еще раз)"
            '<b>Пример:</b> "https://t.me/channel_name - 2888031843 - 1"\n'
            "<b>Важно!</b> Бот должен быть добавлен в этот канал и иметь все права администратора для корректной проверки подписки\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.change_channel)


@admin_router.message(AdminStates.change_channel, is_admin)
async def change_channel(message: Message, state: FSMContext):
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        data = message.text.split('-')  # [ссылка, id, флаг сброса]
        config.bonus_channel_link = data[0].strip()
        config.bonus_channel_id = int('-100' + data[1].strip())
        if int(data[2]):
            db_repo = await db.get_repository()
            need_reset_id = await db_repo.get_with_bonus()
            for id in need_reset_id:
                user = await db_repo.get_user(id)
                user.with_bonus = False
                await db_repo.update_user(user)
        else:
            db_repo = await db.get_repository()
            user = await db_repo.get_user(message.from_user.id)
            user.with_bonus = False
            await db_repo.update_user(user)
        await message.answer("Настройки изменены, вы можете проверить работу по команде /pay")
        await state.clear()
        await db_repo.update_config(config)
    except Exception as e:
        await message.answer(f"Ошибка {e}. Убедитесь, что вы передаете команду в нужном формате")


@admin_router.callback_query(F.data=="change_bonus_for_sub")
async def info_about_change_bonus_for_sub(call: CallbackQuery, state: FSMContext):
    await call.answer()
    text = ("Вы можете изменить бонус за подписку на канал! Просто отправьте мне новый бонус (одно число без пробелов - количество токенов) в следующем сообщении\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.change_bonus_for_sub)


@admin_router.message(AdminStates.change_bonus_for_sub, is_admin)
async def change_bonus_for_sub(message: Message, state: FSMContext):
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        new_bonus = int(message.text)
        config.Bonus_token = new_bonus
        await message.answer(f"Теперь пользователи будут получать бонус {config.Bonus_token} токенов за подписку на канал")
        await state.clear()
        await db_repo.update_config(config)
    except Exception as e:
        await message.answer(f"Ошибка {e}. Убедитесь, что вы вводите одно число без пробелов")


@admin_router.callback_query(F.data=="change_referal_bonus")
async def info_about_change_referal_bonus(call: CallbackQuery, state: FSMContext):
    await call.answer()
    db_repo = await db.get_repository()
    config = await db_repo.get_config()
    text = (f"Вы можете изменить бонус, который получает человек с пополнения своих рефералов.\n"
            f"Сейчас это {config.Referal_bonus}% с каждого пополнения.\n"
            "Просто отправьте новый процент бонуса в следующем сообщении и я установлю его!\n"
            "Для отмены используй команду /cancel")
    await call.message.answer(text)
    await state.set_state(AdminStates.change_referal_bonus)


@admin_router.message(AdminStates.change_referal_bonus, is_admin)
async def change_referal_bonus(message: Message, state: FSMContext):
    try:
        db_repo = await db.get_repository()
        config = await db_repo.get_config()
        new_bonus = int(message.text)
        config.Referal_bonus = new_bonus
        await message.answer(f"Теперь пользователи будут получать бонус {config.Referal_bonus}% токенов за каждое пополнение своих рефералов")
        await state.clear()
        await db_repo.update_config(config)
    except Exception as e:
        await message.answer(f"Ошибка {e}. Убедитесь, что вы вводите одно число без пробелов")