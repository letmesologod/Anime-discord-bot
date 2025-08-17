# anime_scraper.py
import logging
import random
import requests
import cloudscraper
from bs4 import BeautifulSoup

log = logging.getLogger("AnimeScraper")


class AnimeScraper:
    def __init__(self):
        self.base_url = "https://witanime.red"
        self.scraper = cloudscraper.create_scraper(browser="chrome")

    def _fetch_with_cloudscraper(self, url):
        """Try bypassing Cloudflare with cloudscraper"""
        try:
            log.info("🌐 [Cloudscraper] Attempting request...")
            resp = self.scraper.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.text
            log.warning(f"❌ Cloudscraper blocked: {resp.status_code}")
        except Exception as e:
            log.warning(f"❌ Cloudscraper failed: {e}")
        return None

    def _fetch_with_allorigins(self, url):
        """Fallback using AllOrigins proxy API"""
        try:
            log.info("🌐 [AllOrigins] Attempting request...")
            proxy_url = f"https://api.allorigins.win/raw?url={url}"
            resp = requests.get(proxy_url, timeout=10)
            if resp.status_code == 200:
                return resp.text
            log.warning(f"❌ AllOrigins blocked: {resp.status_code}")
        except Exception as e:
            log.warning(f"❌ AllOrigins failed: {e}")
        return None

    def fetch_episodes(self):
        """Scrape latest episodes list from Witanime"""
        url = f"{self.base_url}/"

        # --- Try Cloudscraper ---
        html = self._fetch_with_cloudscraper(url)
        if not html:
            # --- Fallback to AllOrigins ---
            html = self._fetch_with_allorigins(url)

        if not html:
            log.error("🚨 Could not fetch episodes from any source.")
            return []

        soup = BeautifulSoup(html, "html.parser")
        episodes = []

        for card in soup.select(".anime-card-container")[:10]:  # first 10 only
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

        log.info(f"✅ Parsed {len(episodes)} episodes")
        return episodes

