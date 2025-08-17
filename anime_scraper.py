import logging
import random
import time
import json
import os
import cloudscraper
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("AnimeScraper")

class AnimeScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.cache_file = "seen.json"
        self.seen = self._load_seen()

    def _load_seen(self):
        """Load seen episodes from JSON file to avoid duplicates."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_seen(self):
        """Save seen episodes back to disk."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(list(self.seen), f, ensure_ascii=False, indent=2)

    def fetch_episodes(self, retries=5, delay=3):
        url = "https://witanime.red/episode/"
        for attempt in range(1, retries + 1):
            try:
                log.info(f"🌐 [Cloudscraper] Attempt {attempt}")
                res = self.scraper.get(url, timeout=15)
                res.raise_for_status()

                soup = BeautifulSoup(res.text, "html.parser")
                cards = soup.select(".anime-card-container")

                episodes = []
                for card in cards:
                    try:
                        ep_tag = card.select_one(".episodes-card-title h3 a")
                        anime_tag = card.select_one(".anime-card-title h3 a")
                        img_tag = card.select_one("img")

                        ep_link = ep_tag["href"]
                        ep_title = ep_tag.text.strip()
                        anime_title = anime_tag.text.strip()
                        img_url = img_tag["src"] if img_tag else None

                        full_title = f"{anime_title} - {ep_title}"

                        # ✅ skip if already seen
                        if full_title in self.seen:
                            continue

                        episodes.append({
                            "anime": anime_title,
                            "episode": ep_title,
                            "link": ep_link,
                            "image": img_url
                        })
                        self.seen.add(full_title)

                    except Exception as e:
                        log.warning(f"⚠️ Failed to parse episode card: {e}")

                if episodes:
                    self._save_seen()
                    log.info(f"✅ Parsed {len(episodes)} new episode(s) from /episode/")
                    return episodes
                else:
                    log.warning("⚠️ No new episodes found.")
                    return []

            except Exception as e:
                log.warning(f"❌ Attempt {attempt} failed: {e}")
                if attempt < retries:
                    wait = delay + random.uniform(0.5, 2.0)
                    log.info(f"⏳ Retry {attempt}/{retries} in {wait:.1f}s")
                    time.sleep(wait)
                else:
                    log.error("🚨 All retries failed.")
                    return []

