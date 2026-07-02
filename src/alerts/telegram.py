"""Telegram Bot alert sender."""
import asyncio
import httpx
from loguru import logger

from config.settings import settings

BASE = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

URGENCY_EMOJI = {1: "⬜", 2: "🟦", 3: "🟨", 4: "🟧", 5: "🟥"}

GEO_FLAG = {
    "middle_east": "🕌",
    "eastern_europe": "⚔️",
    "asia_pacific": "🌏",
    "global_conflict": "💥",
}


def _build_message(article: dict, analysis: dict) -> str:
    urgency = analysis["urgency"]
    event_type = analysis["event_type"]
    sentiment = analysis["sentiment"]
    geo = analysis.get("geo_categories", [])
    instruments = analysis.get("implied_instruments", [])
    tickers = analysis.get("tickers_mentioned", [])

    emoji = URGENCY_EMOJI.get(urgency, "⬜")
    geo_flags = " ".join(GEO_FLAG.get(g, "") for g in geo)

    lines = [
        f"{emoji} *[U{urgency}] {event_type.upper()}* {geo_flags}",
        f"📰 {article['title']}",
        f"📊 Sentiment: `{sentiment['label']}` ({sentiment['compound']:+.2f})",
    ]
    if instruments:
        lines.append(f"🎯 Instruments: `{' | '.join(instruments[:6])}`")
    if tickers:
        lines.append(f"💹 Tickers: `{' '.join(['$' + t for t in tickers[:8]])}`")
    lines.append(f"🔗 [Read more]({article['url']})")

    return "\n".join(lines)


def send(article: dict, analysis: dict) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram not configured")
        return False

    text = _build_message(article, analysis)
    try:
        resp = httpx.post(
            f"{BASE}/sendMessage",
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False
