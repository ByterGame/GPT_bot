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
            return (str(e), context)
        
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
            return (str(e), context)
        
    def chat_with_gpt5_vision(self, message_text: str, image_urls: Optional[str], context: Optional[List[Dict]]) -> Tuple:
        try:
            user_content = []
            if message_text:
                user_content.append({"type": "text", "text": message_text})
            if image_urls:
                for url in image_urls:
                    user_content.append({"type": "image_url", "image_url": {"url": url}})

            context.append({
                "role": "user",
                "content": user_content
            })

            response = self.openai.chat.completions.create(
                model="gpt-5",
                messages=context
            )

            reply = response.choices[0].message.content
            context.append({"role": "assistant", "content": reply})
            return (reply, context)

        except Exception as e:
            logging.error(f"Ошибка GPT 5 Vision {e}")
            return (str(e), context)
        
    def generate_image_with_dalle(self, prompt: str, context: Optional[List[Dict]], size: str = "1024x1024", n: int = 1) -> Tuple:
        try:
            context.append({"role": "user", "content": prompt if prompt else ""})
            response = self.openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                n=n
            )
            image_urls = [item.url for item in response.data]
            context.append({"role": "assistant", "content": image_urls})
            return (image_urls, context)

        except Exception as e:
            logging.error(f"Ошибка генерации изображения DALL·E: {e}")
            return (str(e), context)
        
    def transcribe_with_whisper(self, audio_file_path: str) -> str:
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return response.text

        except Exception as e:
            logging.error(f"Ошибка Whisper: {e}")
            return str(e)