import json
import logging
from typing import Optional
from database import create_pool
from database.models import User, config_data
from asyncpg import Pool


class DatabaseRepository:
    def __init__(self, pool: Pool):
        self.pool = pool
        
    @classmethod
    async def connect(cls):
        pool = await create_pool()
        return cls(pool)
    
    async def create_user(self, user: User) -> bool:
        """Добавление нового пользователя"""
        query = """
        INSERT INTO users (id, referal_id, is_admin)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO NOTHING
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                user.id,
                user.referal_id,
                user.is_admin
            )
            return result is not None
        

    async def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя"""
        query = "SELECT * FROM users WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, user_id)
            if record:
                context = json.loads(record['context']) if record['context'] else None

                return User(
                    id=record['id'],
                    context=context,
                    gpt_4o_mini_requests=record['gpt_4o_mini_requests'],
                    current_neural_network=record['current_neural_network'],
                    with_bonus=record['with_bonus'],
                    referal_id=record['referal_id'],
                    is_admin=record['is_admin'],
                    balance=record['balance']
                )
            logging.warning(f"Пользователь с id={user_id} не найден в БД")
            return None
        

    async def update_user(self, user: User) -> None:
        """Обновление данных пользователя"""
        query = """
        UPDATE users
        SET 
            context = $1,
            gpt_4o_mini_requests = $2,
            current_neural_network = $3,
            with_bonus = $4,
            referal_id = $5,
            is_admin = $6,
            balance = $7
        WHERE id = $8
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                json.dumps(user.context) if user.context else None,
                user.gpt_4o_mini_requests,
                user.current_neural_network,
                user.with_bonus,
                user.referal_id,
                user.is_admin,
                user.balance,
                user.id
            )

    async def get_referals(self, user_id: int) -> list[User]:
        query = "SELECT * FROM users WHERE referal_id = $1"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)

        referals = []
        for record in rows:
            context = json.loads(record['context']) if record['context'] else None
            referals.append(
                User(
                    id=record['id'],
                    context=context,
                    gpt_4o_mini_requests=record['gpt_4o_mini_requests'],
                    current_neural_network=record['current_neural_network'],
                    with_bonus=record['with_bonus'],
                    referal_id=record['referal_id'],
                    is_admin=record['is_admin'],
                    balance=record['balance']
                )
            )
        return referals
    

    async def get_admins(self) -> list[int]:
        query = "SELECT * FROM users WHERE is_admin = $1"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, True)

        admins_id = []
        for record in rows:
            admins_id.append(record['id'])
        return admins_id
    
    async def get_with_bonus(self) -> list[int]:
        query = "SELECT * FROM users WHERE with_bonus = $1"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, True)

        need_id = []
        for record in rows:
            need_id.append(record['id'])
        return need_id
    

    async def get_all_users_id(self) -> list[int]:
        query = "SELECT * FROM users"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        users_id = []
        for record in rows:
            users_id.append(record['id'])
        return users_id
    

    async def get_config(self) -> config_data:
        query = "SELECT * FROM config_data WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, 1)
            if record:
                packages = json.loads(record['packages']) if record['packages'] else None

                return config_data(
                    id=record['id'],
                    packages=packages,
                    GPT_4o_mini_price = record['GPT_4o_mini_price'],
                    GPT_5_text_price = record['GPT_5_text_price'],
                    GPT_5_vision_price = record['GPT_5_vision_price'],
                    Whisper_price = record['Whisper_price'],
                    Midjourney_mixed_price = record['Midjourney_mixed_price'],
                    Midjourney_fast_price = record['Midjourney_fast_price'],
                    Midjourney_turbo_price = record['Midjourney_turbo_price'],
                    Audio_markup = record['Audio_markup'],
                    Dalle_price=record['Dalle_price'],
                    Bonus_token = record['Bonus_token'],
                    Referal_bonus = record['Referal_bonus'],
                    bonus_channel_link = record['bonus_channel_link'],
                    bot_link_for_referal = record['bot_link_for_referal'],
                    bonus_channel_id = record['bonus_channel_id'],
                    default_4o_limit = record['default_4o_limit'],
                    search_with_links_price=record['search_with_links_price']
                )
            logging.warning(f"config с id=1 не найден в БД")
            return None
    

    async def update_config(self, new_config: config_data):
        query = """
        UPDATE config_data
        SET 
            packages = $1,
            "GPT_4o_mini_price" = $2,
            "GPT_5_text_price" = $3,
            "GPT_5_vision_price" = $4,
            "Whisper_price" = $5,
            "Midjourney_mixed_price" = $6,
            "Midjourney_fast_price" = $7,
            "Midjourney_turbo_price" = $8,
            "Audio_markup" = $9,
            "Bonus_token" = $10,
            "Referal_bonus" = $11,
            bonus_channel_link = $12,
            bot_link_for_referal = $13,
            bonus_channel_id = $14,
            default_4o_limit = $15,
            "Dalle_price" = $16,
            search_with_links_price = $17
        WHERE id = $18
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                json.dumps(new_config.packages) if new_config.packages else "[]",
                new_config.GPT_4o_mini_price,
                new_config.GPT_5_text_price,
                new_config.GPT_5_vision_price,
                new_config.Whisper_price,
                new_config.Midjourney_mixed_price,
                new_config.Midjourney_fast_price,
                new_config.Midjourney_turbo_price,
                new_config.Audio_markup,
                new_config.Bonus_token,
                new_config.Referal_bonus,
                new_config.bonus_channel_link,
                new_config.bot_link_for_referal,
                new_config.bonus_channel_id,
                new_config.default_4o_limit,
                new_config.Dalle_price,
                new_config.search_with_links_price,
                new_config.id
            )
    