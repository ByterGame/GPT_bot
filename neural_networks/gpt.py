import logging


class GPT:
    def __init__(self, openai):
        self.openai = openai

    def chat_with_gpt4o_mini(self, message_text):   
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": message_text if message_text else ""}],
                temperature=0.7
            )
            reply = response.choices[0].message.content
            # logging.info(f"reply - {reply}\n\nresponse - {response}")
            return reply

        except Exception as e:
            logging.error(f"Ошибка GPT 4o mini {e}")
            return (str(e))
        
    def chat_with_gpt5(self, message_text):
        try:
            response = self.openai.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": message_text if message_text else ""}]
            )
            reply = response.choices[0].message.content
            return reply
        except Exception as e:
            logging.error(f"Ошибка GPT 5 {e}")
            return (str(e))