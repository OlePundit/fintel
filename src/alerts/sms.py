"""Twilio SMS — fires ONLY for urgency=5 events."""
from loguru import logger
from twilio.rest import Client

from config.settings import settings


def send_critical(article: dict, analysis: dict) -> bool:
    if analysis.get("urgency", 0) < 5:
        return False
    if not settings.twilio_account_sid:
        logger.warning("Twilio not configured")
        return False

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    geo = ", ".join(analysis.get("geo_categories", []))
    instruments = " | ".join(analysis.get("implied_instruments", [])[:4])
    body = (
        f"🚨 CRITICAL [{analysis['event_type'].upper()}]\n"
        f"{article['title'][:100]}\n"
        f"Geo: {geo or 'n/a'} | Sentiment: {analysis['sentiment']['compound']:+.2f}\n"
        f"Instruments: {instruments or 'n/a'}\n"
        f"{article['url'][:80]}"
    )

    try:
        message = client.messages.create(
            body=body,
            from_=settings.twilio_from_number,
            to=settings.twilio_to_number,
        )
        logger.info(f"SMS sent: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Twilio SMS failed: {e}")
        return False
