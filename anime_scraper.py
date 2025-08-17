import requests
import random
import logging
import time
from bs4 import BeautifulSoup

log = logging.getLogger("AnimeScraper")

class AnimeScraper:
    BASE_URL = "https://witanime.red/"

    def __init__(self, max_retries=5, cooldown=2, max_results=5):
        """
        Anime scraper with proxy rotation & retry logic.
        :param max_retries: how many times to retry before giving up
        :param cooldown: seconds to wait between retries
        :param max_results: maximum episodes to return each run
        """
        self.session = requests.Session()
        self.max_retries = max_retries
        self.cooldown = cooldown
        self.max_results = max_results
        self._last_posted = set()  # track already posted episodes

    def fetch_proxies(self):
        """Fetch fresh proxies from Proxyscrape API"""
        url = (
            "https://api.proxyscrape.com/v3/free-proxy-list/get?"
            "request=displayproxies&protocol=http&timeout=2000&country=all&ssl=all&anonymity=all"
        )
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            proxies = resp.text.splitlines()
            log.info(f"✅ Loaded {len(proxies)} proxies from Proxyscrape")
            return proxies
        except Exception as e:
            log.error(f"❌ Failed to fetch proxies: {e}")
            return []

    def get_latest_episodes(self):
        """Scrape latest episodes with retry, proxy rotation, deduplication & result cap"""
        proxies = self.fetch_proxies()
        episodes = []

        for attempt in range(1, self.max_retries + 1):
            proxy = None
            if proxies:
                proxy = random.choice(proxies)
                proxies.remove(proxy)
                self.session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                log.info(f"🌐 Attempt {attempt}: Using proxy {proxy}")
            else:
                self.session.proxies = {}
                log.info(f"🔄 Attempt {attempt}: Trying direct request")

            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/115.0 Safari/537.36"
                    )
                }
                resp = self.session.get(self.BASE_URL, headers=headers, timeout=10)
                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(".anime-card-container")

                for card in cards:
                    title_el = card.select_one(".anime-card-title h3 a")
                    ep_el = card.select_one(".episodes-card-title h3 a")
                    img_el = card.select_one("img")

                    if title_el and ep_el and img_el:
                        identifier = f"{title_el.text.strip()}-{ep_el.text.strip()}"
                        if identifier in self._last_posted:
                            continue  # skip already posted

                        episodes.append({
                            "title": title_el.text.strip(),
                            "episode": ep_el.text.strip(),
                            "link": ep_el["href"],
                            "image": img_el["src"],
                        })
                        self._last_posted.add(identifier)

                    # limit to avoid spamming Discord
                    if len(episodes) >= self.max_results:
                        break

                if episodes:
                    log.info(f"✅ Successfully scraped {len(episodes)} new episodes")
                    return episodes
                else:
                    log.warning(f"⚠️ No new episodes found on attempt {attempt}")

            except Exception as e:
                log.warning(f"❌ Attempt {attempt} failed: {e}")

            time.sleep(self.cooldown)  # wait before retry

        log.error("🚨 All retries failed.")
        return []

        log.error("🚨 All retries failed.")
        return []


