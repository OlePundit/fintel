"""
SEC EDGAR full-text search + EDGAR RSS feeds.
Covers: S-1 (IPO filings), 8-K (material events), 13F (institutional), 4 (insider trades).
All free, no API key needed.
"""
import httpx
import feedparser
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

EDGAR_RSS_FEEDS = {
    "edgar_s1":  "https://efts.sec.gov/LATEST/search-index?q=%22S-1%22&dateRange=custom&startdt={today}&forms=S-1&hits.hits._source=period_of_report,file_date,display_names,period_of_report&hits.hits.total.value=true&_source=period_of_report,file_date&hits.hits.highlight.file_date=true",
    "edgar_8k":  "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&dateb=&owner=include&count=40&output=atom",
    "edgar_ipo": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=S-1&dateb=&owner=include&count=20&output=atom",
    "edgar_insider": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&dateb=&owner=include&count=40&output=atom",
}

HEADERS = {
    "User-Agent": "fintel-bot contact@youremail.com",  # EDGAR requires this
    "Accept-Encoding": "gzip, deflate",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=3, max=15))
def _fetch(url: str) -> list[dict]:
    resp = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
    feed = feedparser.parse(resp.text)
    items = []
    for entry in feed.entries:
        items.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "body": entry.get("summary", ""),
            "published_at": entry.get("updated", entry.get("published", "")),
        })
    return items


def collect() -> list[dict]:
    results = []
    for source, url in EDGAR_RSS_FEEDS.items():
        try:
            items = _fetch(url)
            for item in items:
                item["source"] = "edgar"
            results.extend(items)
            logger.debug(f"EDGAR [{source}] fetched {len(items)} items")
        except Exception as e:
            logger.warning(f"EDGAR [{source}] failed: {e}")
    return results
