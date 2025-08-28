import aiohttp
from aiogram import types
from config import MJ_KEY


async def download_photo(image_url: str, task_id: int):
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as download_session:
            async with download_session.get(
                image_url, 
                headers={"X-API-KEY": MJ_KEY}
            ) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    return types.BufferedInputFile(image_data, filename=f"image{task_id}.png")                  
                else:
                    return None
                    
    except Exception as e:
        return None