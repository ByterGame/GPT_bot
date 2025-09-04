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
    referal_id: int = None
    is_admin: bool = False
