from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
import pytz

class User(BaseModel):
    id: int
    end_subscription_day: datetime = datetime.now(pytz.timezone('Europe/Moscow'))
    context: Optional[List[Dict]] = None
    gpt_4o_mini_requests: int = 30
    gpt_5_requests: int = 50
    gpt_5_vision_requests: int = 25
    dalle_requests: int = 25
    whisper_requests: int = 30
    midjourney_requests: int = 20
    search_with_links_requests: int = 25
    current_neural_network: int = 0
