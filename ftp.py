import os
import re
import discord
from typing import Any
from urllib.parse import unquote, urlparse

# --- your existing config ---
TOKEN = os.environ['discordtoken']

#FTP GIF
#GIF_RESPONSE = "https://tenor.com/view/ftp-detroit-lions-packers-fuck-gif-26012280"

#Kevin GIF
GIF_RESPONSE = "https://tenor.com/view/green-bay-packers-suck-gif-3881298770212525772"

#Commanders GIF
#GIF_RESPONSE = "https://tenor.com/view/squabble-jayden-daniels-gif-17131932023536614817"

PACKERS_PATTERN = re.compile(
    r"(packers|green\s+bay|jordan\s+love|matt\s+lafleur|bart\s+starr|lambeau|favre|aaron\s+rodgers|bears\s+still\s+suck|green\sand\sgold|reggie\s+white|clay\s+matthews|qaaron|rodgers|micah|micah\s+parsons|parsons|#1)(?:\b|$)",
    re.IGNORECASE,
)


# If you want player names to count too, add them here:
# PACKERS_PATTERN = re.compile(r"\b(...|reggie\s+white|...) \b", re.IGNORECASE)

intents = discord.Intents(messages=True, message_content=True, guilds=True, guild_messages=True)
#intents.message_content = True
client = discord.Client(intents=intents)

GIF_DOMAINS = {"tenor.com", "media.tenor.com", "giphy.com", "i.giphy.com"}
DISCORD_EXTERNAL_HOSTS = {"images-ext-1.discordapp.net", "media.discordapp.net"}

def _any_string_fields(obj: Any):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _any_string_fields(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _any_string_fields(v)

def unwrap_discord_external(url: str) -> str:
    """
    Turn:
      https://images-ext-1.discordapp.net/external/.../https/media.tenor.com/.../reggie-white.png
    into:
      https://media.tenor.com/.../reggie-white.png
    """
    if not url:
        return url
    try:
        p = urlparse(url)
        if p.netloc in DISCORD_EXTERNAL_HOSTS and "/external/" in p.path:
            # The real URL is typically after '/external/.../(http|https)/'
            # Split on '/http' or '/https' and rebuild.
            parts = p.path.split("/https/", 1)
            scheme = "https"
            if len(parts) == 1:
                parts = p.path.split("/http/", 1)
                scheme = "http"
            if len(parts) == 2:
                inner = parts[1]  # e.g. media.tenor.com/.../reggie-white.png
                return f"{scheme}://{inner}"
    except Exception:
        pass
    return url

def _matches_packers(text: str) -> bool:
    return bool(PACKERS_PATTERN.search(text or ""))

def _url_tokens(url: str) -> str:
    """
    Return a token string from URL path & filename so slugs like 'reggie-white'
    are searchable by your regex.
    """
    try:
        u = unwrap_discord_external(url)
        u = unquote(u)
        parsed = urlparse(u)
        # combine host + path to give regex more context
        return f"{parsed.netloc} {parsed.path}".replace("/", " ")
    except Exception:
        return url or ""

async def respond_if_match(message: discord.Message):
    if message.author == client.user:
        return

    # 1) plain text
    if _matches_packers(message.content):
        await message.channel.send(GIF_RESPONSE)
        return

    # 2) attachments
    for a in message.attachments:
        cand = " ".join([
            a.filename or "",
            _url_tokens(a.url or ""),
            _url_tokens(a.proxy_url or ""),
            (a.content_type or "")
        ])
        if _matches_packers(cand):
            await message.channel.send(GIF_RESPONSE)
            return

    # 3) embeds (deep scan + URL unwrapping)
    for e in message.embeds:
        ed = e.to_dict()
        for s in _any_string_fields(ed):
            # look at raw string and also at unwrapped URL tokens
            test_blob = f"{s} {_url_tokens(s)}"
            if _matches_packers(test_blob):
                await message.channel.send(GIF_RESPONSE)
                return

    # 4) stickers
    for st in getattr(message, "stickers", []) or []:
        if _matches_packers(getattr(st, "name", "") or ""):
            await message.channel.send(GIF_RESPONSE)
            return

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    await respond_if_match(message)

@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    await respond_if_match(after)

client.run(TOKEN)
