import requests
from bs4 import BeautifulSoup

class AnimeScraper:
    BASE_URL = "https://witanime.red/"

    def __init__(self):
        # Fake browser headers to avoid 403 errors
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def get_latest_episodes(self):
        """Scrape latest episodes from witanime.red"""
        episodes = []

        try:
            response = requests.get(self.BASE_URL, headers=self.headers, timeout=10)
            response.raise_for_status()  # raises exception if 403/404/500

            soup = BeautifulSoup(response.text, "html.parser")

            # Adjust this selector depending on the site’s HTML structure
            # Example: looking for episode cards inside <div class="episodes-card">
            cards = soup.select("div.episodes-card")  # <-- may need tweaking

            for card in cards:
                title_tag = card.select_one("h3 a")
                image_tag = card.select_one("img")

                if not title_tag or not image_tag:
                    continue

                title = title_tag.get_text(strip=True)
                link = title_tag["href"]
                image = image_tag.get("src")

                episodes.append({
                    "title": title,
                    "link": link,
                    "image": image,
                })

        except Exception as e:
            print(f"[AnimeScraper] Error: {e}")

        return episodes
