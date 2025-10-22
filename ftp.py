import discord
import re

# ⚠️ Replace with your actual bot token and desired GIF URL
TOKEN = "token"
GIF_RESPONSE = "https://tenor.com/view/ftp-detroit-lions-packers-fuck-gif-26012280"  # Example: anti-Packers gif

# Regex to match "packers" (case-insensitive)
PACKERS_PATTERN = re.compile(r'\b(packers|green\s+bay|jordan\s+love|matt\s+lafleur|bart\s+starr|Lambeau|favre|bears\s+still\s+suck)\b', re.IGNORECASE)


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check for embeds (e.g. Tenor/GIPHY GIFs)
    for embed in message.embeds:
        if PACKERS_PATTERN.search(str(embed.title)) or PACKERS_PATTERN.search(str(embed.url)):
            await message.channel.send(GIF_RESPONSE)
            return

    # Check for GIFs uploaded as attachments
    for attachment in message.attachments:
        if attachment.filename.lower().endswith('.gif') and PACKERS_PATTERN.search(attachment.filename):
            await message.channel.send(GIF_RESPONSE)
            return

    # Check regular text message content
    if PACKERS_PATTERN.search(message.content):
        await message.channel.send(GIF_RESPONSE)

client.run(TOKEN)
