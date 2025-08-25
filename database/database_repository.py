import json
import logging
from typing import Optional
from database import create_pool
from database.models import User
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
        INSERT INTO users (id)
        VALUES ($1)
        ON CONFLICT (id) DO NOTHING
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                user.id
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
                    end_subscription_day=record['end_subscription_day'],
                    gpt_4o_mini_requests=record['gpt_4o_mini_requests'],
                    gpt_5_requests=record['gpt_5_requests'],
                    gpt_5_vision_requests=record['gpt_5_vision_requests'],
                    dalle_requests = record['dalle_requests'],
                    whisper_requests = record['whisper_requests'],
                    midjourney_requests = record['midjourney_requests'],
                    search_with_links_requests = record['search_with_links_requests'],
                    current_neural_network=record['current_neural_network'],
                    with_bonus=record['with_bonus']
                )
            logging.warning(f"Пользователь с id={user_id} не найден в БД")
            return None
        

    async def update_user(self, user: User) -> None:
        """Обновление данных пользователя"""
        query = """
        UPDATE users
        SET 
            context = $1,
            end_subscription_day = $2,
            gpt_4o_mini_requests = $3,
            gpt_5_requests = $4,
            gpt_5_vision_requests = $5,
            dalle_requests = $6,
            whisper_requests = $7,
            midjourney_requests = $8,
            search_with_links_requests = $9,
            current_neural_network = $10,
            with_bonus = $11
        WHERE id = $12
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                json.dumps(user.context) if user.context else None,
                user.end_subscription_day,
                user.gpt_4o_mini_requests,
                user.gpt_5_requests,
                user.gpt_5_vision_requests,
                user.dalle_requests,
                user.whisper_requests,
                user.midjourney_requests,
                user.search_with_links_requests,
                user.current_neural_network,
                user.with_bonus,
                user.id
            )
    