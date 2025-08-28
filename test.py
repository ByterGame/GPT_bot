import asyncio
import aiohttp
from aiogram import types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from tqdm import tqdm
from create_bot import bot
from config import MJ_KEY

async def main(image_url: str, user_id: int):
    print("Начало функции")
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as download_session:
            async with download_session.get(
                image_url, 
                headers={"X-API-KEY": MJ_KEY}
            ) as resp:
                
                if resp.status == 200:
                    print("Соединение установлено")
                    total_size = int(resp.headers.get('content-length', 0))
                    print(f"Размер файла: {total_size / 1024 / 1024:.2f} MB")
                    progress_bar = tqdm(
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                        desc="Скачивание"
                    )
                    chunks = []
                    async for chunk in resp.content.iter_chunked(8192):
                        chunks.append(chunk)
                        progress_bar.update(len(chunk))
                    progress_bar.close()
                    print("Файл успешно скачан")
                    image_data = b''.join(chunks)
                    print(f"Размер в памяти: {len(image_data) / 1024 / 1024:.2f} MB")
                    photo_file = types.BufferedInputFile(image_data, filename="image.png")
                    await bot.send_photo(user_id, photo=photo_file)
                    print("Фото отправлено в Telegram")
                    
                else:
                    print(f"Ошибка HTTP: {resp.status}")
                    
    except Exception as e:
        print(f"Произошла ошибка: {e}")
