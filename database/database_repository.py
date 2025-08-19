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
    
    async def create_user(self, user: User):
        pass
    