import logging
from typing import Optional, List, Dict, Tuple


class GPT:
    def __init__(self, openai):
        self.openai = openai

    def chat_with_gpt4o_mini(self, message_text: str, context: Optional[List[Dict]]) -> Tuple:   
        try:
            context.append({"role": "user", "content": message_text if message_text else ""})
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=context,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            context.append({"role": "assistant", "content": reply})
            return (reply, context)

        except Exception as e:
            logging.error(f"Ошибка GPT 4o mini {e}")
            return (str(e), [])
        
    def chat_with_gpt5(self, message_text: str, context: Optional[List[Dict]]) -> str:
        try:
            context.append({"role": "user", "content": message_text if message_text else ""})
            response = self.openai.chat.completions.create(
                model="gpt-5",
                messages=context
            )
            reply = response.choices[0].message.content
            context.append({"role": "assistant", "content": reply})
            return (reply, context)
        except Exception as e:
            logging.error(f"Ошибка GPT 5 {e}")
            return (str(e), [])