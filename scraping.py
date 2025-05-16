import time
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection

# Bright Data browser proxy auth
AUTH = "brd-customer-hl_c6d8089a-zone-scraping_browser1:vzuwwrzzb697"
SBR_WEBDRIVER = f"https://{AUTH}@brd.superproxy.io:9515"


def scrape_website(url: str, scroll_attempts: int = 12, pause: float = 1.5) -> str:
    """Return the *fully scrolled* HTML of the page."""
    print("Launching Chrome (Bright Data)…")
    conn = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")

    with Remote(conn, options=ChromeOptions()) as driver:
        driver.get(url)

        # ── Scroll until no more content loads or attempts exhausted ──
        last_h = driver.execute_script("return document.documentElement.scrollHeight")
        for _ in range(scroll_attempts):
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(pause)
            new_h = driver.execute_script("return document.documentElement.scrollHeight")
            if new_h == last_h:
                break
            last_h = new_h

        return driver.page_source


def _video_id_from_href(href: str) -> str | None:
    """Extract the 11-char YouTube ID from /watch?v=ID or /shorts/ID."""
    if not href:
        return None
    if "/watch" in href:
        qs = parse_qs(urlparse(href).query)
        return qs.get("v", [None])[0]
    if "/shorts/" in href:
        return href.split("/shorts/")[-1].split("?")[0]
    return None


def extract_video_data(html: str, base_url: str) -> list[dict]:
    """Return a list of dicts: title, url, thumb, views, date."""
    soup = BeautifulSoup(html, "html.parser")
    videos = []

    for node in soup.select("ytd-grid-video-renderer, ytd-rich-item-renderer"):
        # -- link & video ID ---------------------------------------------------
        link = node.select_one("a#thumbnail")
        href = link.get("href") if link else ""
        vid = _video_id_from_href(href)
        if not vid:
            continue

        video_url = f"https://www.youtube.com/watch?v={vid}"
        thumbnail = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"  # always exists

        # -- title -------------------------------------------------------------
        title_node = (
            node.select_one("a#video-title")
            or node.select_one("yt-formatted-string#video-title")
        )
        title = (
            title_node.get("title")            # attribute (if present)
            or title_node.get_text(strip=True) # fallback to text
            if title_node else "(no title)"
        )

        # -- views & date ------------------------------------------------------
        views = date = ""
        spans = node.select("#metadata-line span, #metadata span.inline-metadata-item")
        if len(spans) >= 2:
            views = spans[0].get_text(strip=True)
            date = spans[1].get_text(strip=True)

        videos.append(
            {
                "title": title,
                "video_url": video_url,
                "thumbnail": thumbnail,
                "views": views,
                "date": date,
            }
        )
    return videos
