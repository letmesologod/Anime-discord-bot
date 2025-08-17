import discord
from discord.ext import commands, tasks
from anime_scraper import AnimeScraper
import logging
import os

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
scraper = AnimeScraper()

# Load channel ID from environment variable
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))  # fallback to 0 if not set

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    if CHANNEL_ID == 0:
        logger.error("DISCORD_CHANNEL_ID not set! Bot will not send messages.")
    else:
        check_new_episodes.start()

@tasks.loop(minutes=10)
async def check_new_episodes():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        try:
            episodes = scraper.get_latest_episodes()
            for ep in episodes:
                embed = discord.Embed(
                    title=ep["title"],
                    url=ep["link"],
                    description=f"New episode released: {ep['title']}",
                    color=discord.Color.blue()
                )
                embed.set_image(url=ep["image"])
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching episodes: {e}")

