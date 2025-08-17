#!/usr/bin/env python3
"""
Discord Anime Episode Notifier Bot
Monitors witanime.red for new episodes and sends Discord notifications
"""

import logging
import os
from threading import Thread

from bot_config import bot
from keep_alive import run_flask_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot and keep-alive server"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return

    # Start Flask keep-alive server
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    # Start the Discord bot
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
