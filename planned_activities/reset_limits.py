from database.core import db
from database.models import User
import json
from config import DEFAULT_GPT5_VISION_LIMIT, DEFAULT_GPT_4O_LIMIT, DEFAULT_GPT_5_LIMIT, DALLE_LIMIT, WHISPER_LIMIT, MIDJOURNEY_LIMIT, SEARCH_WITH_LINKS_LIMIT


async def reset_limits():
    db_repo = await db.get_repository()
    
    query = "SELECT * FROM users"
    async with db_repo.pool.acquire() as conn:
        records = await conn.fetch(query)
    
    for record in records:
        user = User(
            id=record['id'],
            end_subscription_day=record['end_subscription_day'],
            context=json.loads(record['context']) if record['context'] else None,
            gpt_4o_mini_requests=DEFAULT_GPT_4O_LIMIT,
            gpt_5_requests=DEFAULT_GPT_5_LIMIT,
            gpt_5_vision_requests=DEFAULT_GPT5_VISION_LIMIT,
            dalle_requests=DALLE_LIMIT,
            whisper_requests=WHISPER_LIMIT,
            midjourney_requests=MIDJOURNEY_LIMIT,
            search_with_links_requests=SEARCH_WITH_LINKS_LIMIT,
            with_bonus=record['with_bonus']
        )
        await db_repo.update_user(user)
