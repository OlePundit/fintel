"""RSS feed collector — financial news + geopolitical sources."""
import feedparser
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Financial + geopolitical RSS feeds (all free, no auth needed)
FEEDS: dict[str, str] = {
    # Market news
    "reuters":      "https://feeds.reuters.com/reuters/businessNews",
    "reuters_world": "https://feeds.reuters.com/Reuters/worldNews",
    "cnbc":         "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "cnbc_world":   "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "marketwatch":  "https://feeds.marketwatch.com/marketwatch/topstories/",
    "ft":           "https://www.ft.com/?format=rss",
    "seeking_alpha": "https://seekingalpha.com/feed.xml",
    # Geopolitical / world
    "bbc_world":    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "ap_world":     "https://rsshub.app/apnews/topics/world-news",
    "al_jazeera":   "https://www.aljazeera.com/xml/rss/all.xml",
    "guardian_world": "https://www.theguardian.com/world/rss",
    # Commodities / energy
    "oilprice":     "https://oilprice.com/rss/main",
    "platts":       "https://www.spglobal.com/commodityinsights/en/rss-feed/oil",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; fintel-bot/1.0; +https://github.com/you/fintel)"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _fetch_feed(url: str) -> list[dict]:
    resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
    feed = feedparser.parse(resp.text)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "body": entry.get("summary", ""),
            "published_at": entry.get("published", ""),
        })
    return articles


def collect(max_per_feed: int = 30) -> list[dict]:
    results = []
    for source, url in FEEDS.items():
        try:
            items = _fetch_feed(url)[:max_per_feed]
            for item in items:
                item["source"] = source
            results.extend(items)
            logger.debug(f"RSS [{source}] fetched {len(items)} items")
        except Exception as e:
            logger.warning(f"RSS [{source}] failed: {e}")
    return results
