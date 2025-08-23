# import discord
# import re
# import asyncio
# from create_bot import bot
# from config import DISCORD_TOKEN, CHANNEL_ID


# intents = discord.Intents.default()
# intents.messages = True
# client = discord.Client(intents=intents)

# @client.event
# async def on_ready():
#     print(f"Logged in as {client.user}")

# async def send_prompt(prompt: str):
#     channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
#     await channel.send(f"/imagine prompt {prompt}")

# @client.event
# async def on_message(message):
#     if message.author.id == 936929561302675456 and message.attachments:
#         match = re.search(r"\[tg:(\d+)\]", message.content)
#         if match:
#             tg_id = int(match.group(1))
#             for attachment in message.attachments:
#                 await bot.send_photo(tg_id, attachment.url)

# async def start_discord():
#     async with client:
#         await client.start(DISCORD_TOKEN)
