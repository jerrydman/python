"""
Author: Jerry Reid
Instagram & TikTok Embed Fixer Discord Bot
5/28/2026
"""

import os
import re
import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("embed-fixer")

# ── Config ────────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

INSTAGRAM_FIX_DOMAIN = "kkinstagram.com"
TIKTOK_FIX_DOMAIN    = "tnktok.com"

INSTAGRAM_RE = re.compile(
    r"(https?://(?:www\.)?instagram\.com/"
    r"(?:p|reel|tv|stories)/[^\s<>\"]+)",
    re.IGNORECASE,
)

TIKTOK_RE = re.compile(
    r"(https?://(?:(?:www\.|vm\.)?tiktok\.com)/[^\s<>\"]+)",
    re.IGNORECASE,
)

# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fix_instagram(url: str) -> str:
    return re.sub(r"(?:www\.)?instagram\.com", INSTAGRAM_FIX_DOMAIN, url, flags=re.IGNORECASE)


def fix_tiktok(url: str) -> str:
    return re.sub(r"(?:www\.|vm\.)?tiktok\.com", TIKTOK_FIX_DOMAIN, url, flags=re.IGNORECASE)


def should_skip(url: str, content: str) -> bool:
    if f"<{url}>" in content:
        return True
    idx = content.find(url)
    if idx > 0 and content[idx - 1] == "$":
        return True
    return False


def has_instagram(content: str) -> bool:
    return any(not should_skip(url, content) for url in INSTAGRAM_RE.findall(content))


def find_and_fix(content: str) -> tuple[str, int]:
    fixed = content
    count = 0

    for url in INSTAGRAM_RE.findall(content):
        if not should_skip(url, content):
            fixed = fixed.replace(url, fix_instagram(url))
            count += 1

    for url in TIKTOK_RE.findall(content):
        if not should_skip(url, content):
            fixed = fixed.replace(url, fix_tiktok(url))
            count += 1

    return fixed, count


async def get_or_create_webhook(channel: discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    for wh in webhooks:
        if wh.user == bot.user:
            return wh
    return await channel.create_webhook(name="Embed Fixer")


# ── Events ────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    invite = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            manage_webhooks=True,
            read_message_history=True,
            add_reactions=True,
        ),
    )
    log.info(f"Invite URL: {invite}")


@bot.event
async def on_message(message: discord.Message):
    if not message.guild or message.author.bot:
        return

    await bot.process_commands(message)

    fixed_content, count = find_and_fix(message.content)

    if count == 0:
        return

    needs_embed_check = has_instagram(message.content)

    try:
        webhook = await get_or_create_webhook(message.channel)
        original_content = message.content
        await message.delete()
        sent = await webhook.send(
            content=fixed_content,
            username=message.author.display_name,
            avatar_url=message.author.display_avatar.url,
            wait=True,
        )
        await sent.add_reaction("❌")

        if needs_embed_check:
            await asyncio.sleep(3)
            sent = await message.channel.fetch_message(sent.id)
            if not sent.embeds:
                await sent.delete()
                await message.channel.send(original_content)
                log.info(
                    f"Sensitive content detected, restored original link for "
                    f"{message.author} in #{message.channel}"
                )
                return

        log.info(f"Fixed {count} link(s) for {message.author} in #{message.channel}")

    except discord.Forbidden:
        log.warning(
            f"Missing permissions in #{message.channel} ({message.guild}). "
            "Falling back to plain reply."
        )
        await message.reply(
            f"**Fixed embed{'s' if count > 1 else ''}:**\n{fixed_content}",
            mention_author=False,
        )


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot or str(reaction.emoji) != "❌":
        return

    msg = reaction.message
    if not msg.webhook_id:
        return

    try:
        webhook = await bot.fetch_webhook(msg.webhook_id)
        if webhook.user != bot.user:
            return
    except discord.NotFound:
        return

    if user.display_name == msg.author.name:
        await msg.delete()
        log.info(f"{user} deleted their fixed message in #{msg.channel}")



@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx: commands.Context):
    synced = await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"✅ Synced {len(synced)} command(s) to this server.")


@bot.tree.command(name="fix", description="Manually fix an Instagram or TikTok link")
async def fix_command(interaction: discord.Interaction, url: str):
    if INSTAGRAM_RE.match(url):
        await interaction.response.send_message(fix_instagram(url))
    elif TIKTOK_RE.match(url):
        await interaction.response.send_message(fix_tiktok(url))
    else:
        await interaction.response.send_message(
            "❌ That doesn't look like an Instagram or TikTok URL.", ephemeral=True
        )


@bot.tree.command(name="ignore-me", description="Stop the bot from fixing your links")
async def ignore_me(interaction: discord.Interaction):
    await interaction.response.send_message(
        "⚠️ Ignore list not yet implemented. "
        "Prefix any link with `$` or wrap it in `<>` to skip fixing it.",
        ephemeral=True,
    )


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set. Add it to your .env file.")
    bot.run(DISCORD_TOKEN)