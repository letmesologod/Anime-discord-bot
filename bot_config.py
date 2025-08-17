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

# Load channel ID from env
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))


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
            if not episodes:
                await channel.send("⚠️ Could not fetch new episodes right now. Please try again later.")
                logger.warning("No episodes scraped — possibly blocked or site down.")
                return

            for ep in episodes[:3]:  # limit to 3 to avoid spam
                embed = discord.Embed(
                    title=ep["title"],
                    url=ep["link"],
                    description=f"New episode released: {ep['title']}",
                    color=discord.Color.blue()
                )
                if ep.get("image"):
                    embed.set_image(url=ep["image"])
                await channel.send(embed=embed)

        except Exception as e:
            error_msg = f"❌ Error fetching episodes: {e}"
            await channel.send(error_msg)
            logger.error(error_msg)


# ------------------------------
# Manual command: !latest
# ------------------------------
@bot.command(name="latest")
async def latest(ctx):
    """Fetch the latest episodes manually"""
    try:
        episodes = scraper.get_latest_episodes()
        if not episodes:
            await ctx.send("⚠️ Could not fetch new episodes right now. Please try again later.")
            return

        for ep in episodes[:3]:  # show only top 3 latest
            embed = discord.Embed(
                title=ep["title"],
                url=ep["link"],
                description=f"New episode released: {ep['title']}",
                color=discord.Color.green()
            )
            if ep.get("image"):
                embed.set_image(url=ep["image"])
            await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error fetching episodes: {e}")
        logger.error(f"[!latest] Error: {e}")


