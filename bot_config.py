# bot_config.py
import os
import logging
import discord
from discord.ext import tasks, commands
from anime_scraper import AnimeScraper

# --- Logging ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot_config")

# --- Discord Intents ---
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages

# --- Bot Setup ---
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Scraper ---
scraper = AnimeScraper()

# --- Config ---
DISCORD_CHANNEL = os.getenv("DISCORD_CHANNEL") or os.getenv("DISCORD_CHANNEL_ID")
if not DISCORD_CHANNEL:
    log.error("❌ No channel ID set. Please add DISCORD_CHANNEL env var.")
else:
    log.info(f"📡 Sending updates to channel: {DISCORD_CHANNEL}")

posted_episodes = set()  # memory cache so we don’t spam repeats


# --- Bot Events ---
@bot.event
async def on_ready():
    log.info(f"✅ Bot logged in as {bot.user}")
    check_new_episodes.start()


# --- Background Task ---
@tasks.loop(minutes=5.0)  # check every 5 minutes
async def check_new_episodes():
    channel = bot.get_channel(int(DISCORD_CHANNEL))
    if not channel:
        log.error("❌ Channel not found — check DISCORD_CHANNEL env var")
        return

    episodes = scraper.fetch_episodes()
    if not episodes:
        log.warning("⚠️ No episodes scraped — possibly blocked or site down.")
        return

    new_eps = [ep for ep in episodes if ep["link"] not in posted_episodes]

    for ep in new_eps:
        embed = discord.Embed(
            title=f"{ep['title']} - {ep['episode']}",
            url=ep['link'],
            description="🎬 New episode is available now!",
            color=discord.Color.purple(),
        )
        if ep["image"]:
            embed.set_thumbnail(url=ep["image"])

        await channel.send(embed=embed)
        posted_episodes.add(ep["link"])

        log.info(f"📢 Posted: {ep['title']} {ep['episode']}")


# --- Commands ---
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("🏓 Pong! I’m alive.")

@bot.command(name="latest")
async def latest(ctx):
    episodes = scraper.fetch_episodes()
    if not episodes:
        await ctx.send("⚠️ Could not fetch episodes right now.")
        return

    for ep in episodes[:5]:  # show last 5
        embed = discord.Embed(
            title=f"{ep['title']} - {ep['episode']}",
            url=ep['link'],
            description="📺 Latest episode update",
            color=discord.Color.green(),
        )
        if ep["image"]:
            embed.set_thumbnail(url=ep["image"])
        await ctx.send(embed=embed)


# --- Run ---
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    log.error("❌ DISCORD_TOKEN is missing in env vars")
else:
    bot.run(TOKEN)



