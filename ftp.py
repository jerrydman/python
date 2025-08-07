import discord
import random
import re
import os

# Replace with your bot token
TOKEN = "bot_token"
GIF_URL = "https://tenor.com/view/ftp-detroit-lions-packers-fuck-gif-26012280"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

PACKERS_PATTERN = re.compile(r'\bpackers\b', re.IGNORECASE)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if PACKERS_PATTERN.search(message.content):
        await message.channel.send(GIF_URL)

client.run(TOKEN)