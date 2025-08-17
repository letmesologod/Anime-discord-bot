import requests
from bs4 import BeautifulSoup
import cloudscraper
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnimeScraper")

class AnimeScraper:
    BASE_URL = "https://witanime.red/"

    def __init__(self):
        # Create scraper (helps bypass Cloudflare)
        self.scraper = cloudscraper.create_scraper(browser="chrome")

        # Fetch proxies automatically
        self.proxies = self.get_free_proxies()
        if not self.proxies:
            logger.warning("No proxies found, scraping without proxy.")
        else:
            logger.info(f"Fetched {len(self.proxies)} proxies")

    def get_free_proxies(self):
        """Scrape free HTTPS proxies from free-proxy-list.net"""
        url = "https://free-proxy-list.net/"
        proxies = []

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"id": "proxylisttable"})

            for row in table.tbody.find_all("tr"):
                cols = row.find_all("td")
                ip = cols[0].text.strip()
                port = cols[1].text.strip()
                https = cols[6].text.strip()

                if https == "yes":
                    proxy = f"http://{ip}:{port}"
                    proxies.append(proxy)

        except Exception as e:
            logger.error(f"Error fetching proxies: {e}")

        return proxies

    def get_latest_episodes(self):
        """Scrape latest episodes from Witanime"""
        episodes = []
        try:
            proxy = random.choice(self.proxies) if self.proxies else None
            proxies = {"http": proxy, "https": proxy} if proxy else None
            if proxy:
                logger.info(f"Using proxy: {proxy}")

            response = self.scraper.get(self.BASE_URL, proxies=proxies, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("div.anime-card-container")

            for card in cards:
                ep_tag = card.select_one("div.episodes-card-title h3 a")
                img_tag = card.select_one("img.img-responsive")
                anime_tag = card.select_one("div.anime-card-title h3 a")

                if not ep_tag or not img_tag:
                    continue

                ep_title = ep_tag.get_text(strip=True)
                ep_link = ep_tag["href"]
                ep_image = img_tag.get("src")
                anime_title = anime_tag.get_text(strip=True) if anime_tag else "Unknown Anime"

                full_title = f"{anime_title} - {ep_title}"

                episodes.append(
                    {"title": full_title, "link": ep_link, "image": ep_image}
                )

            logger.info(f"✅ Scraped {len(episodes)} episodes")

        except Exception as e:
            logger.error(f"Error fetching episodes: {e}")

        return episodes


# 🔹 Debug: Run scraper manually
if __name__ == "__main__":
    scraper = AnimeScraper()
    eps = scraper.get_latest_episodes()
    for ep in eps[:5]:  # show first 5 episodes
        print(ep)


