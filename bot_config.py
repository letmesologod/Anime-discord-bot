import os
import logging
import discord
from discord.ext import commands, tasks
from anime_scraper import AnimeScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)7s] %(name)s: %(message)s")
log = logging.getLogger("bot_config")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
scraper = AnimeScraper()

DISCORD_CHANNEL = os.getenv("DISCORD_CHANNEL") or os.getenv("DISCORD_CHANNEL_ID")

@bot.event
async def on_ready():
    log.info(f"✅ Bot logged in as {bot.user}")
    if DISCORD_CHANNEL:
        log.info(f"📡 Sending updates to channel: {DISCORD_CHANNEL}")
        check_new_episodes.start()
    else:
        log.error("❌ Channel not found — check DISCORD_CHANNEL env var")

@tasks.loop(minutes=10)
async def check_new_episodes():
    channel = bot.get_channel(int(DISCORD_CHANNEL))
    if not channel:
        log.error("❌ Target channel not found.")
        return

    episodes = scraper.fetch_episodes()
    for ep in episodes:
        embed = discord.Embed(
            title=f"{ep['anime']} — {ep['episode']}",
            url=ep["link"],
            description=f"New episode released: **{ep['episode']}**",
            color=discord.Color.blue()
        )
        if ep["image"]:
            embed.set_thumbnail(url=ep["image"])
        await channel.send(embed=embed)
        log.info(f"📢 Posted: {ep['anime']} {ep['episode']}")

# 🔹 Commands
@bot.command(name="latest")
async def latest(ctx):
    """Show latest 5 episodes from /episode/."""
    episodes = scraper.fetch_episodes()
    if not episodes:
        await ctx.send("⚠️ No new episodes found.")
        return
    for ep in episodes[:5]:
        embed = discord.Embed(
            title=f"{ep['anime']} — {ep['episode']}",
            url=ep["link"],
            color=discord.Color.green()
        )
        if ep["image"]:
            embed.set_thumbnail(url=ep["image"])
        await ctx.send(embed=embed)

@bot.command(name="anime")
async def anime(ctx, *, name: str):
    """Search for episodes by anime name."""
    episodes = scraper.fetch_episodes()
    results = [ep for ep in episodes if name.lower() in ep["anime"].lower()]
    if not results:
        await ctx.send(f"⚠️ No episodes found for `{name}`")
        return
    for ep in results[:5]:
        embed = discord.Embed(
            title=f"{ep['anime']} — {ep['episode']}",
            url=ep["link"],
            color=discord.Color.purple()
        )
        if ep["image"]:
            embed.set_thumbnail(url=ep["image"])
        await ctx.send(embed=embed)



