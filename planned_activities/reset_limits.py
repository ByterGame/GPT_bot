from database.core import db
from database.models import User

DEFAULT_GPT_4O_LIMIT = 30
DEFAULT_GPT_5_LIMIT = 50
DEFAULT_GPT5_VISION_LIMIT = 25

async def reset_limits():
    db_repo = await db.get_repository()
    
    query = "SELECT * FROM users"
    async with db_repo.pool.acquire() as conn:
        records = await conn.fetch(query)
    
    for record in records:
        user = User(
            id=record['id'],
            end_subscription_day=record['end_subscription_day'],
            context=record['context'],
            gpt_4o_mini_requests=DEFAULT_GPT_4O_LIMIT,
            gpt_5_requests=DEFAULT_GPT_5_LIMIT,
            gpt_5_vision_requests=DEFAULT_GPT5_VISION_LIMIT
        )
        await db_repo.update_user(user)
