import os
import logging
import random
import time
import requests
import cloudscraper
from bs4 import BeautifulSoup

log = logging.getLogger("AnimeScraper")

class AnimeScraper:
    def __init__(self, url="https://witanime.red/"):
        self.url = url
        self.scraper = cloudscraper.create_scraper()  # Cloudflare bypass
        self.proxies = []
        self.max_retries = 5
        self.timeout = 10

    def fetch_proxies(self):
        """Fetch fresh proxies from proxyscrape API"""
        try:
            resp = requests.get(
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=1000&country=all&ssl=all&anonymity=all"
            )
            if resp.status_code == 200:
                self.proxies = list(set(resp.text.splitlines()))
                log.info(f"✅ Loaded {len(self.proxies)} proxies from Proxyscrape")
            else:
                log.warning("⚠️ Failed to fetch proxies, status %s", resp.status_code)
        except Exception as e:
            log.error("❌ Error fetching proxies: %s", e)

    def get(self, url):
        """Try cloudscraper first, fallback to proxies if needed"""
        headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"
            ])
        }

        # 1️⃣ Try cloudscraper
        for attempt in range(1, self.max_retries + 1):
            try:
                log.info(f"🌐 [Cloudscraper] Attempt {attempt}")
                resp = self.scraper.get(url, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                return resp
            except Exception as e:
                log.warning(f"❌ Cloudscraper attempt {attempt} failed: {e}")
                time.sleep(2)

        # 2️⃣ Fallback: try random proxies
        if not self.proxies:
            self.fetch_proxies()

        for attempt in range(1, self.max_retries + 1):
            if not self.proxies:
                break
            proxy = random.choice(self.proxies)
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            try:
                log.info(f"🌐 [Proxy] Attempt {attempt} with {proxy}")
                resp = requests.get(url, headers=headers, proxies=proxies, timeout=self.timeout)
                resp.raise_for_status()
                return resp
            except Exception as e:
                log.warning(f"❌ Proxy attempt {attempt} with {proxy} failed: {e}")
                time.sleep(2)

        log.error("🚨 All retries failed.")
        return None

    def fetch_episodes(self):
        """Scrape episodes from Witanime"""
        resp = self.get(self.url)
        if not resp:
            log.error("❌ Could not fetch episodes at all.")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        episodes = []
        for card in soup.select(".anime-card-container"):
            title_el = card.select_one(".anime-card-title h3 a")
            episode_el = card.select_one(".episodes-card-title h3 a")
            img_el = card.select_one("img")

            if title_el and episode_el and img_el:
                episodes.append({
                    "title": title_el.text.strip(),
                    "episode": episode_el.text.strip(),
                    "url": episode_el["href"],
                    "image": img_el["src"]
                })

        log.info(f"✅ Scraped {len(episodes)} episodes")
        return episodes



