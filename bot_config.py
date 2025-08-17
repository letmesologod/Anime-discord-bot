import os
import logging
import asyncio
import discord
from discord.ext import tasks, commands
from anime_scraper import AnimeScraper

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bot_config")

# ---------- Config ----------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # set in Koyeb secrets
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL", "0"))  # channel to post episodes
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))  # default 10 min

# ---------- Bot Setup ----------
intents = discord.Intents.default()
intents.message_content = True  # needed for commands
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Scraper ----------
scraper = AnimeScraper(max_retries=5, cooldown=2, max_results=5)

# ---------- Background Task ----------
@tasks.loop(seconds=CHECK_INTERVAL)
async def fetch_and_post():
    """Background task that fetches new episodes & posts to Discord"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        log.error("❌ Channel not found — check DISCORD_CHANNEL env var")
        return

    try:
        episodes = scraper.get_latest_episodes()
        if not episodes:
            await channel.send("⚠️ No new episodes found (possibly blocked or site down).")
            log.warning("⚠️ No episodes scraped — possibly blocked or site down.")
            return

        for ep in episodes:
            embed = discord.Embed(
                title=f"{ep['title']} - {ep['episode']}",
                url=ep["link"],
                description="New episode available 🎉",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=ep["image"])
            embed.set_footer(text="Anime Notif Bot • Powered by Witanime")
            await channel.send(embed=embed)
            await asyncio.sleep(2)  # small delay to avoid spam

    except Exception as e:
        log.error(f"🚨 Error in fetch_and_post: {e}", exc_info=True)
        if channel:
            await channel.send("🚨 Error while fetching episodes, check logs.")

# ---------- Bot Events ----------
@bot.event
async def on_ready():
    log.info(f"✅ Bot logged in as {bot.user}")
    if not fetch_and_post.is_running():
        fetch_and_post.start()

@bot.command()
async def ping(ctx):
    """Simple healthcheck command"""
    await ctx.send("🏓 Pong! Bot is alive.")

@bot.command()
async def latest(ctx, count: int = 3):
    """Fetch latest X episodes immediately"""
    try:
        episodes = scraper.get_latest_episodes()
        if not episodes:
            await ctx.send("⚠️ No new episodes found.")
            return

        for ep in episodes[:count]:
            embed = discord.Embed(
                title=f"{ep['title']} - {ep['episode']}",
                url=ep["link"],
                description="Latest episode 🔎",
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=ep["image"])
            await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send("❌ Failed to fetch latest episodes.")
        log.error(f"Error in !latest command: {e}", exc_info=True)

# ---------- Run ----------
if __name__ == "__main__":
    if not DISCORD_TOKEN or CHANNEL_ID == 0:
        log.error("❌ Missing DISCORD_TOKEN or DISCORD_CHANNEL in environment")
    else:
        bot.run(DISCORD_TOKEN)





