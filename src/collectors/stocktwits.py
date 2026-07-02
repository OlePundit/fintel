"""
StockTwits free API — no auth required for trending streams.
Covers retail sentiment on instruments + tickers.
"""
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

BASE = "https://api.stocktwits.com/api/2"

# Watch these symbols for instrument market sentiment
SYMBOLS = [
    "SPY", "QQQ", "DIA",           # Broad market
    "GLD", "SLV",                   # Gold / silver
    "USO", "OIL", "XLE",           # Crude / energy
    "TLT", "IEF",                   # Bonds
    "UUP",                          # Dollar
    "NVDA", "TSM", "SOXX",         # Semis (geopolitical proxy)
    "LMT", "RTX", "NOC",           # Defense
    "BTC.X", "ETH.X",              # Crypto
]


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=8))
def _fetch_symbol(symbol: str) -> list[dict]:
    resp = httpx.get(
        f"{BASE}/streams/symbol/{symbol}.json",
        timeout=10,
    )
    resp.raise_for_status()
    messages = resp.json().get("messages", [])
    items = []
    for msg in messages:
        items.append({
            "source": "stocktwits",
            "title": f"[{symbol}] {msg.get('body', '')[:100]}",
            "url": f"https://stocktwits.com/message/{msg.get('id', '')}",
            "body": msg.get("body", ""),
            "published_at": msg.get("created_at", ""),
        })
    return items


def collect() -> list[dict]:
    results = []
    for symbol in SYMBOLS:
        try:
            items = _fetch_symbol(symbol)
            results.extend(items)
            logger.debug(f"StockTwits [{symbol}] fetched {len(items)} messages")
        except Exception as e:
            logger.warning(f"StockTwits [{symbol}] failed: {e}")
    return results
