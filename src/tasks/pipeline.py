"""
Main processing pipeline.
collect → deduplicate → keyword filter → sentiment + urgency → alert
"""
import json
from loguru import logger

from src.tasks.celery_app import app
from src.storage.db import SessionLocal, save_article, is_duplicate
from src.analysis.keywords import match as kw_match
from src.analysis.urgency import compute as urgency_compute
from src.alerts import telegram, email_digest
from config.settings import settings


def _process_items(items: list[dict]) -> int:
    """Core pipeline: analyze and alert. Returns count of items alerted."""
    alerted = 0
    with SessionLocal() as session:
        for item in items:
            url = item.get("url", "")
            title = item.get("title", "")
            if not url or not title:
                continue

            if is_duplicate(session, url, title):
                continue

            # Combine title + body for analysis
            text = f"{title}. {item.get('body', '')}"

            # Keyword gate — drop irrelevant articles before any further work
            km = kw_match(text)
            if not km.matched:
                # Still store with matched=False for deduplication
                save_article(session, {
                    "source": item.get("source", "unknown"),
                    "title": title,
                    "url": url,
                    "body": item.get("body", ""),
                    "published_at": item.get("published_at"),
                    "matched": False,
                })
                continue

            # Full analysis
            analysis = urgency_compute(text, km, item.get("source", ""))
            analysis["geo_categories"] = km.geo_categories
            analysis["fin_categories"] = km.fin_categories
            analysis["implied_instruments"] = km.implied_instruments
            analysis["tickers_mentioned"] = km.tickers_mentioned

            # Persist
            saved = save_article(session, {
                "source": item.get("source", "unknown"),
                "title": title,
                "url": url,
                "body": item.get("body", ""),
                "published_at": item.get("published_at"),
                "matched": True,
                "urgency": analysis["urgency"],
                "event_type": analysis["event_type"],
                "sentiment_compound": analysis["sentiment"]["compound"],
                "geo_categories": json.dumps(km.geo_categories),
                "fin_categories": json.dumps(km.fin_categories),
                "tickers": json.dumps(km.tickers_mentioned),
                "instruments": json.dumps(km.implied_instruments),
            })

            if not saved:
                continue

            # Alert thresholds
            if analysis["urgency"] >= settings.min_alert_urgency:
                sent = telegram.send(item, analysis)
                if sent:
                    alerted += 1
                    logger.info(
                        f"ALERT U{analysis['urgency']} [{analysis['event_type']}] "
                        f"geo={km.geo_categories} | {title[:60]}"
                    )

    return alerted


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_rss(self):
    try:
        from src.collectors.rss import collect
        items = collect(max_per_feed=30)
        alerted = _process_items(items)
        logger.info(f"RSS pipeline: {len(items)} collected, {alerted} alerted")
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_gdelt(self):
    try:
        from src.collectors.gdelt import collect
        items = collect()
        alerted = _process_items(items)
        logger.info(f"GDELT pipeline: {len(items)} collected, {alerted} alerted")
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_edgar(self):
    try:
        from src.collectors.edgar import collect
        items = collect()
        alerted = _process_items(items)
        logger.info(f"EDGAR pipeline: {len(items)} collected, {alerted} alerted")
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_reddit(self):
    try:
        from src.collectors.reddit import collect
        items = collect(limit=25)
        alerted = _process_items(items)
        logger.info(f"Reddit pipeline: {len(items)} collected, {alerted} alerted")
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_stocktwits(self):
    try:
        from src.collectors.stocktwits import collect
        items = collect()
        alerted = _process_items(items)
        logger.info(f"StockTwits pipeline: {len(items)} collected, {alerted} alerted")
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task
def send_daily_digest():
    email_digest.send_digest()
