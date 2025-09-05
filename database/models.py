from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
import pytz
from config import DEFAULT_GPT_4O_LIMIT, DEFAULT_PROMPT

class User(BaseModel):
    id: int
    context: Optional[List[Dict]] = [{"role": "system", "content": DEFAULT_PROMPT}]
    gpt_4o_mini_requests: int = DEFAULT_GPT_4O_LIMIT
    balance: int = 0
    current_neural_network: int = 0
    with_bonus: bool = False
    referal_id: Optional[int] = None
    is_admin: bool = False


class config_data(BaseModel):
    id: int
    packages: List[Dict] = []
    GPT_4o_mini_price: int = 1
    GPT_5_text_price: int = 5
    GPT_5_vision_price: int = 10
    Whisper_price: int = 3
    Dalle_price: int = 15
    search_with_links_price: int = 5
    Midjourney_mixed_price: int = 15
    Midjourney_fast_price: int = 45
    Midjourney_turpo_price: int = 70
    Audio_markup: int = 2
    Bonus_token: int = 50
    Referal_bonus: int = 10
    bonus_channel_link: str = "t.me/test_byter"
    bot_link_for_referal: str = "https://t.me/byter_test_bot"
    bonus_channel_id: int = -1002888031843
    default_4o_limit: int = 30
