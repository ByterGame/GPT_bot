import asyncpg
from database.database_repository import DatabaseRepository

class Database:
    def __init__(self):
        self._repository = None

    async def connect(self):
        self._repository = await DatabaseRepository.connect()
        return self

    async def get_repository(self):
        if self._repository is None:
            raise RuntimeError("Database not connected!")
        return self._repository

db = Database()