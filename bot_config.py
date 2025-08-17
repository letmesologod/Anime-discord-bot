import discord
from discord.ext import commands, tasks
from anime_scraper import AnimeScraper
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Scraper instance (with proxy + retry logic)
scraper = AnimeScraper()

# Load Discord channel ID from env variable
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))  # put your channel ID in Koyeb env vars

@bot.event
async def on_ready():
    logger.info(f"✅ Bot logged in as {bot.user}")
    check_new_episodes.start()

@tasks.loop(minutes=10)
async def check_new_episodes():
    """Check for new anime episodes every 10 minutes and post in Discord."""
    if CHANNEL_ID == 0:
        logger.error("❌ DISCORD_CHANNEL_ID not set in environment variables.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        logger.error(f"❌ Channel with ID {CHANNEL_ID} not found.")
        return

    try:
        episodes = scraper.get_latest_episodes()
        if not episodes:
            logger.warning("⚠️ No episodes scraped — possibly blocked or site down.")
            return

        for ep in episodes:
            embed = discord.Embed(
                title=ep["title"],
                url=ep["link"],
                description=f"📺 New episode released: {ep['title']}",
                color=discord.Color.blue()
            )
            if ep.get("image"):
                embed.set_image(url=ep["image"])

            await channel.send(embed=embed)
            logger.info(f"✅ Posted episode: {ep['title']}")

    except Exception as e:
        logger.error(f"❌ Error fetching episodes: {e}")



