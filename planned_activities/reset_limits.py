from database.core import db
from database.models import User
import json
from config import DEFAULT_GPT_4O_LIMIT
                    


async def reset_limits():
    db_repo = await db.get_repository()
    
    query = "SELECT * FROM users"
    async with db_repo.pool.acquire() as conn:
        records = await conn.fetch(query)
    
    for record in records:
        user = User(
            id=record['id'],
            context=json.loads(record['context']) if record['context'] else None,
            gpt_4o_mini_requests=DEFAULT_GPT_4O_LIMIT,
            with_bonus=record['with_bonus'],
            balance=record['balance'],
            current_neural_network=record['current_neural_network'],
            is_admin=record['is_admin'],
            referal_id=record['referal_id']
        )
        await db_repo.update_user(user)
