import discord
from discord.ext import commands, tasks
from anime_scraper import AnimeScraper
import logging

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
scraper = AnimeScraper()

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    check_new_episodes.start()

@tasks.loop(minutes=10)
async def check_new_episodes():
    channel_id = 123456789012345678  # replace with your Discord channel ID
    channel = bot.get_channel(channel_id)
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


    for ep in eps[:5]:  # show first 5 episodes
        print(ep)



