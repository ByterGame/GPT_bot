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
        INSERT INTO users (id, referal_id)
        VALUES ($1, $2)
        ON CONFLICT (id) DO NOTHING
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                user.id,
                user.referal_id
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
                    is_admin=record['is_admin']
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
                    is_admin=record['is_admin']
                )
            )
        return referals
    