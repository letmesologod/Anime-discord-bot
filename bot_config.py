import os
import logging
import asyncio
import discord
from discord.ext import commands, tasks
from anime_scraper import AnimeScraper

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("bot_config")

# --- Discord setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

scraper = AnimeScraper()
posted_episodes = set()  # store posted episodes so we don’t duplicate

@bot.event
async def on_ready():
    log.info(f"✅ Bot logged in as {bot.user}")
    if CHANNEL_ID == 0:
        log.error("❌ Channel not found — check DISCORD_CHANNEL_ID env var")
        return
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        log.error("❌ Could not fetch channel from ID")
        return
    log.info(f"📡 Sending updates to channel: {channel.name}")
    check_new_episodes.start()

@tasks.loop(minutes=5)  # 🔄 check every 5 minutes
async def check_new_episodes():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        log.error("❌ Channel not found inside task loop")
        return

    episodes = scraper.fetch_episodes()
    if not episodes:
        log.warning("⚠️ No episodes scraped — possibly blocked or site down.")
        return

    new_eps = [ep for ep in episodes if ep["url"] not in posted_episodes]

    if not new_eps:
        log.info("ℹ️ No new episodes found this cycle.")
        return

    for ep in new_eps:
        embed = discord.Embed(
            title=f"{ep['title']} - {ep['episode']}",
            url=ep["url"],
            description="New episode available!",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ep["image"])
        await channel.send(embed=embed)

        posted_episodes.add(ep["url"])  # mark as posted
        log.info(f"📢 Posted update: {ep['title']} - {ep['episode']}")

# --- Commands ---
@bot.command()
async def ping(ctx):
    """Test if bot is alive"""
    await ctx.send("🏓 Pong!")

@bot.command()
async def latest(ctx, count: int = 3):
    """Fetch latest X episodes manually (default: 3)"""
    episodes = scraper.fetch_episodes()
    if not episodes:
        await ctx.send("⚠️ Could not fetch episodes.")
        return
    for ep in episodes[:count]:
        embed = discord.Embed(
            title=f"{ep['title']} - {ep['episode']}",
            url=ep["url"],
            description="Latest episode",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=ep["image"])
        await ctx.send(embed=embed)

# --- Start bot ---
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.error("❌ No DISCORD_TOKEN set in environment variables")
    else:
        bot.run(DISCORD_TOKEN)





