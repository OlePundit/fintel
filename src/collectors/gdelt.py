"""
GDELT 2.0 DOC API collector.
Free, no auth, real-time global event coverage — excellent for geopolitical signals.
Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Query themes that map to instrument-moving geopolitical events
GDELT_QUERIES = [
    # Conflict / military
    "Iran Israel war OR strike OR missile",
    "Russia Ukraine war OR attack OR offensive",
    "China Taiwan military OR invasion OR blockade",
    "North Korea missile OR nuclear",
    "Houthi Red Sea shipping attack",
    # Commodity disruption
    "Strait of Hormuz blockade OR tanker",
    "OPEC oil production cut OR increase",
    "natural gas pipeline explosion OR disruption",
    # Sanctions / financial
    "sanctions Russia OR Iran OR China",
    "export controls semiconductors OR chips",
    # Market systemic
    "bank collapse OR bank run",
    "sovereign debt default",
]

HEADERS = {"User-Agent": "fintel-bot/1.0"}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _query_gdelt(query: str, mode: str = "artlist", max_records: int = 10) -> list[dict]:
    params = {
        "query": query,
        "mode": mode,
        "maxrecords": max_records,
        "format": "json",
        "timespan": "1h",  # last 1 hour only — we run frequently
    }
    resp = httpx.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for item in data.get("articles", []):
        articles.append({
            "source": "gdelt",
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "body": item.get("seendate", "") + " " + item.get("domain", ""),
            "published_at": item.get("seendate", ""),
        })
    return articles


def collect() -> list[dict]:
    results = []
    seen_urls: set[str] = set()
    for query in GDELT_QUERIES:
        try:
            items = _query_gdelt(query)
            for item in items:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    results.append(item)
            logger.debug(f"GDELT [{query[:40]}...] → {len(items)} items")
        except Exception as e:
            logger.warning(f"GDELT query failed [{query[:40]}]: {e}")
    return results
