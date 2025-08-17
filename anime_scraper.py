# anime_scraper.py
import logging
import random
import time
from urllib.parse import urljoin

import requests
import cloudscraper
from bs4 import BeautifulSoup

log = logging.getLogger("AnimeScraper")
log.setLevel(logging.INFO)


class AnimeScraper:
    def __init__(self, base_url: str = "https://witanime.red", timeout: int = 12, max_retries: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        # cloudscraper handles most CF pages better than plain requests
        self.scraper = cloudscraper.create_scraper(browser={"custom": "Mozilla/5.0"})

    # ------------- HTTP helpers -------------
    def _fetch_cloudscraper(self, url: str) -> str | None:
        try:
            log.info("🌐 [Cloudscraper] GET %s", url)
            r = self.scraper.get(url, timeout=self.timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            log.warning("❌ Cloudscraper failed: %s", e)
            return None

    def _fetch_allorigins(self, url: str) -> str | None:
        try:
            proxy = f"https://api.allorigins.win/raw?url={url}"
            log.info("🌐 [AllOrigins] GET %s", proxy)
            r = requests.get(proxy, timeout=self.timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            log.warning("❌ AllOrigins failed: %s", e)
            return None

    def _get_html(self, url: str) -> str | None:
        """Try cloudscraper first, then AllOrigins, with retries/backoff."""
        for attempt in range(1, self.max_retries + 1):
            html = self._fetch_cloudscraper(url)
            if not html:
                html = self._fetch_allorigins(url)

            if html:
                return html

            if attempt < self.max_retries:
                wait = random.uniform(2, 5)
                log.info("⏳ Retry %d/%d in %.1fs", attempt, self.max_retries, wait)
                time.sleep(wait)

        log.error("🚨 All retries failed for %s", url)
        return None

    # ------------- Parsing -------------
    def _abs(self, maybe_url: str | None) -> str | None:
        if not maybe_url:
            return None
        return urljoin(self.base_url + "/", maybe_url)

    def _parse_episode_cards(self, soup: BeautifulSoup, limit: int) -> list[dict]:
        episodes: list[dict] = []

        # Primary layout (matches the snippet you showed earlier)
        cards = soup.select(".anime-card-container")
        if not cards:
            # Fallback: some themes use different wrappers
            cards = soup.select(".anime-card, .episodes-card, .post, article")

        for card in cards:
            try:
                # Episode link (must contain /episode/)
                ep_a = card.select_one(".episodes-card-title h3 a")
                if not ep_a:
                    # Fallback: any anchor that links to /episode/
                    ep_a = card.select_one('a[href*="/episode/"]')
                if not ep_a:
                    continue  # skip non-episode cards

                ep_link = self._abs(ep_a.get("href"))
                if not ep_link or "/episode/" not in ep_link:
                    continue

                ep_label = (ep_a.get_text(strip=True) or "Episode").strip()

                # Anime title
                title_a = card.select_one(".anime-card-title h3 a") or card.select_one('a[href*="/anime/"]')
                title = (title_a.get_text(strip=True) if title_a else "").strip() or "Unknown Title"

                # Image (poster/thumbnail)
                img = None
                img_tag = card.select_one("img")
                if img_tag and img_tag.get("src"):
                    img = self._abs(img_tag["src"])

                episodes.append({
                    "title": title,
                    "episode": ep_label,
                    "link": ep_link,
                    "image": img,
                })

                if len(episodes) >= limit:
                    break
            except Exception as e:
                log.warning("⚠️ Parse error on a card: %s", e)

        return episodes

    # ------------- Public API -------------
    def fetch_episodes(self, limit: int = 10) -> list[dict]:
        """
        Fetch the newest episodes specifically from /episode/ (not the homepage).
        Returns a list of dicts: {title, episode, link, image}
        """
        url = f"{self.base_url}/episode/"
        html = self._get_html(url)
        if not html:
            log.error("❌ Could not fetch the /episode/ page.")
            return []

        soup = BeautifulSoup(html, "html.parser")
        episodes = self._parse_episode_cards(soup, limit=limit)

        # As a safety filter, ensure we only return /episode/ links
        episodes = [e for e in episodes if "/episode/" in (e.get("link") or "")]
        log.info("✅ Parsed %d episode(s) from /episode/", len(episodes))
        return episodes



