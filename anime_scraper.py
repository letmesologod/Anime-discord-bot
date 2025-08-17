import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class AnimeScraper:
    def __init__(self):
        self.base_url = "https://witanime.red"
        self.session = requests.Session()
        self.last_seen = set()

    def get_latest_episodes(self):
        url = f"{self.base_url}/"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        episodes = []
        for item in soup.select("div.episodes-card"):
            title = item.select_one("h3").get_text(strip=True)
            link = item.select_one("a")["href"]
            image = item.select_one("img")["src"]

            if link not in self.last_seen:
                self.last_seen.add(link)
                episodes.append({
                    "title": title,
                    "link": link,
                    "image": image
                })
        return episodes
