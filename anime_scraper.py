# anime_scraper.py
import logging
import time
import random
import requests
import cloudscraper
from bs4 import BeautifulSoup

log = logging.getLogger("AnimeScraper")
log.setLevel(logging.INFO)

class AnimeScraper:
    def __init__(self, base_url="https://witanime.red", max_retries=5, timeout=15):
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.scraper = cloudscraper.create_scraper()

    def get(self, url):
        """Fetch a URL using AllOrigins first, fallback to Cloudscraper."""
        for attempt in range(1, self.max_retries + 1):
            # --- Try AllOrigins (Free API) ---
            try:
                proxy_url = f"https://api.allorigins.win/raw?url={url}"
                log.info(f"🌐 [AllOrigins] Attempt {attempt} for {url}")
                resp = requests.get(proxy_url, timeout=self.timeout)
                resp.raise_for_status()
                log.info("✅ Success via AllOrigins")
                return resp
            except Exception as e:
                log.warning(f"❌ AllOrigins attempt {attempt} failed: {e}")

            # --- Fallback to Cloudscraper ---
            try:
                log.info(f"🌐 [Cloudscraper] Attempt {attempt} for {url}")
                resp = self.scraper.get(url, timeout=self.timeout)
                resp.raise_for_status()
                log.info("✅ Success via Cloudscraper")
                return resp
            except Exception as e:
                log.warning(f"❌ Cloudscraper attempt {attempt} failed: {e}")

            # wait before retry
            sleep_time = random.uniform(2, 5)
            log.info(f"⏳ Waiting {sleep_time:.1f}s before retry...")
            time.sleep(sleep_time)

        log.error("🚨 All retries failed. Returning None")
        return None

    def fetch_latest_episodes(self):
        """Scrape the latest episodes list from Witanime."""
        url = f"{self.base_url}/"
        resp = self.get(url)
        if not resp:
            log.error("❌ Could not fetch homepage.")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        episodes = []

        for card in soup.select(".anime-card-container")[:10]:  # limit for performance
            try:
                title_tag = card.select_one(".anime-card-title h3 a")
                ep_tag = card.select_one(".episodes-card-title h3 a")
                img_tag = card.select_one("img")

                title = title_tag.text.strip() if title_tag else "Unknown Title"
                ep = ep_tag.text.strip() if ep_tag else "Unknown Episode"
                link = ep_tag["href"] if ep_tag else self.base_url
                img = img_tag["src"] if img_tag else None

                episodes.append({
                    "title": title,
                    "episode": ep,
                    "link": link,
                    "image": img,
                })
            except Exception as e:
                log.warning(f"⚠️ Failed parsing card: {e}")

        log.info(f"✅ Fetched {len(episodes)} episodes")
        return episodes


