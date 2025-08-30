from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
import pytz
from config import (DEFAULT_GPT5_VISION_LIMIT, DEFAULT_GPT_4O_LIMIT, 
                    DEFAULT_GPT_5_LIMIT, DALLE_LIMIT, WHISPER_LIMIT, 
                    MIDJOURNEY_LIMIT, SEARCH_WITH_LINKS_LIMIT, DEFAULT_PROMPT)

class User(BaseModel):
    id: int
    end_subscription_day: datetime = datetime.now(pytz.timezone('Europe/Moscow'))
    context: Optional[List[Dict]] = [{"role": "system", "content": DEFAULT_PROMPT}]
    gpt_4o_mini_requests: int = DEFAULT_GPT_4O_LIMIT
    gpt_5_requests: int = DEFAULT_GPT_5_LIMIT
    gpt_5_vision_requests: int = DEFAULT_GPT5_VISION_LIMIT
    dalle_requests: int = DALLE_LIMIT
    whisper_requests: int = WHISPER_LIMIT
    midjourney_requests: int = MIDJOURNEY_LIMIT
    search_with_links_requests: int = SEARCH_WITH_LINKS_LIMIT
    current_neural_network: int = 0
    with_bonus: bool = False
