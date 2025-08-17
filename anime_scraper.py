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
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Each episode card
            cards = soup.select("div.anime-card-container")

            for card in cards:
                # Episode info
                ep_tag = card.select_one("div.episodes-card-title h3 a")
                img_tag = card.select_one("img.img-responsive")
                anime_tag = card.select_one("div.anime-card-title h3 a")

                if not ep_tag or not img_tag:
                    continue

                ep_title = ep_tag.get_text(strip=True)  # e.g. "الحلقة 7"
                ep_link = ep_tag["href"]
                ep_image = img_tag.get("src")
                anime_title = anime_tag.get_text(strip=True) if anime_tag else "Unknown Anime"

                # Combine anime + episode in title
                full_title = f"{anime_title} - {ep_title}"

                episodes.append(
                    {
                        "title": full_title,
                        "link": ep_link,
                        "image": ep_image,
                    }
                )

        except Exception as e:
            print(f"[AnimeScraper] Error fetching episodes: {e}")

        return episodes
