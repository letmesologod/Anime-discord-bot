import requests
from bs4 import BeautifulSoup
import cloudscraper
import logging
import random
import time
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnimeScraper")

class AnimeScraper:
    BASE_URL = "https://witanime.red/"
    CACHE_FILE = "working_proxy.json"

    def __init__(self):
        self.scraper = cloudscraper.create_scraper(browser="chrome")
        self.proxies = self.get_free_proxies()

        # Try load last known working proxy
        self.working_proxy = self.load_cached_proxy()

        if not self.proxies:
            logger.warning("⚠️ No proxies found, will try direct only.")
        else:
            logger.info(f"✅ Found {len(self.proxies)} fresh proxies")

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

    def load_cached_proxy(self):
        """Load last working proxy from file"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r") as f:
                    proxy = json.load(f).get("proxy")
                    logger.info(f"🔄 Loaded cached proxy: {proxy}")
                    return proxy
            except Exception:
                pass
        return None

    def save_cached_proxy(self, proxy):
        """Save working proxy to file"""
        try:
            with open(self.CACHE_FILE, "w") as f:
                json.dump({"proxy": proxy}, f)
            logger.info(f"💾 Cached working proxy: {proxy}")
        except Exception as e:
            logger.error(f"Error saving proxy cache: {e}")

    def fetch_with_retry(self, url, max_retries=5):
        """Try cached proxy, then random fresh ones, then direct"""
        proxies_pool = self.proxies.copy()
        random.shuffle(proxies_pool)

        # If we have a cached proxy, try it first
        if self.working_proxy:
            proxies_pool.insert(0, self.working_proxy)

        # Always try direct last
        proxies_pool.append(None)

        for attempt, proxy in enumerate(proxies_pool[:max_retries], 1):
            try:
                if proxy:
                    logger.info(f"🔄 Attempt {attempt}: Trying proxy {proxy}")
                    proxies = {"http": proxy, "https": proxy}
                else:
                    logger.info(f"🔄 Attempt {attempt}: Trying direct request")
                    proxies = None

                response = self.scraper.get(url, proxies=proxies, timeout=15)
                response.raise_for_status()

                # Save successful proxy
                if proxy:
                    self.save_cached_proxy(proxy)
                    self.working_proxy = proxy

                return response.text

            except Exception as e:
                logger.warning(f"❌ Attempt {attempt} failed ({proxy}): {e}")
                time.sleep(2)

        logger.error("🚨 All retries failed.")
        return None

    def get_latest_episodes(self):
        """Scrape latest episodes from Witanime"""
        episodes = []
        html = self.fetch_with_retry(self.BASE_URL)

        if not html:
            logger.error("❌ Could not fetch episodes at all.")
            return episodes

        try:
            soup = BeautifulSoup(html, "html.parser")
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
            logger.error(f"Error parsing episodes: {e}")

        return episodes


# 🔹 Debug mode
if __name__ == "__main__":
    scraper = AnimeScraper()
    eps = scraper.get_latest_episodes()
    for ep in eps[:5]:
        print(ep)
