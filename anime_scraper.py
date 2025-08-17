import requests
import random
import logging
import time
from bs4 import BeautifulSoup

log = logging.getLogger("AnimeScraper")

# ✅ Fetch fresh free proxies from Proxyscrape API
def fetch_proxies():
    url = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=2000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        proxies = resp.text.splitlines()
        log.info(f"✅ Loaded {len(proxies)} proxies from Proxyscrape")
        return proxies
    except Exception as e:
        log.error(f"❌ Failed to fetch proxies: {e}")
        return []

# ✅ Scrape episodes with retry + proxy rotation
def scrape_episodes(max_retries=5):
    url = "https://witanime.red/"
    proxies = fetch_proxies()
    session = requests.Session()

    for attempt in range(1, max_retries + 1):
        # Choose proxy or go direct
        proxy = None
        if proxies:
            proxy = random.choice(proxies)
            proxies.remove(proxy)
            session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            log.info(f"🌐 Attempt {attempt}: Using proxy {proxy}")
        else:
            session.proxies = {}
            log.info(f"🔄 Attempt {attempt}: Trying direct request")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/115.0 Safari/537.36"
            }
            resp = session.get(url, headers=headers, timeout=10)
            resp.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(resp.text, "html.parser")
            episodes = []

            for card in soup.select(".anime-card-container"):
                title_el = card.select_one(".anime-card-title h3 a")
                ep_el = card.select_one(".episodes-card-title h3 a")
                img_el = card.select_one("img")

                if title_el and ep_el and img_el:
                    episodes.append({
                        "title": title_el.text.strip(),
                        "episode": ep_el.text.strip(),
                        "link": ep_el["href"],
                        "image": img_el["src"],
                    })

            if episodes:
                log.info(f"✅ Successfully scraped {len(episodes)} episodes")
                return episodes
            else:
                log.warning(f"⚠️ No episodes found on attempt {attempt}")

        except Exception as e:
            log.warning(f"❌ Attempt {attempt} failed: {e}")

        time.sleep(2)  # wait before retry

    log.error("🚨 All retries failed.")
    return []

