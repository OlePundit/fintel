"""
Rules-based urgency scorer (1–5).
Combines sentiment, keyword categories, and source weight.
"""
from .keywords import MatchResult
from .sentiment import score as sentiment_score

# Source credibility weight (higher = trust it more for urgency)
SOURCE_WEIGHT: dict[str, float] = {
    "reuters": 1.3,
    "bloomberg": 1.3,
    "ft": 1.2,
    "wsj": 1.2,
    "cnbc": 1.1,
    "marketwatch": 1.0,
    "seeking_alpha": 0.9,
    "gdelt": 1.2,
    "edgar": 1.4,
    "reddit": 0.7,
    "stocktwits": 0.7,
    "google_news": 0.9,
}

# Categories that immediately bump urgency
HIGH_URGENCY_FIN = {"ipo", "price_move", "sec_event", "macro"}
HIGH_URGENCY_GEO = {"middle_east", "eastern_europe", "asia_pacific"}


def compute(text: str, match: MatchResult, source: str) -> dict:
    """
    Returns urgency int 1-5, sentiment dict, and event_type string.
    """
    sent = sentiment_score(text)
    weight = SOURCE_WEIGHT.get(source, 1.0)
    base = 1

    # Geo bump
    if match.geo_categories:
        geo_hits = set(match.geo_categories)
        base = max(base, 3 if geo_hits & HIGH_URGENCY_GEO else 2)

    # Financial category bump
    if match.fin_categories:
        fin_hits = set(match.fin_categories)
        if fin_hits & HIGH_URGENCY_FIN:
            base = max(base, 3)

    # Strong negative sentiment is urgency-worthy
    if sent["compound"] <= -0.5:
        base = max(base, 4)
    elif sent["compound"] <= -0.25:
        base = max(base, 3)

    # Strong geo + strong negative → max alert
    if match.geo_categories and sent["compound"] <= -0.4:
        base = max(base, 4)

    # SEC filings are always at least 3
    if "sec_event" in match.fin_categories:
        base = max(base, 3)

    # Instrument market impact with strong geo → 5
    if match.implied_instruments and set(match.geo_categories) & HIGH_URGENCY_GEO and sent["compound"] <= -0.3:
        base = 5

    # Apply source weight and clamp
    urgency = min(5, round(base * weight))

    # Derive event_type label
    if match.geo_categories:
        event_type = "geopolitical"
    elif "ipo" in match.fin_categories:
        event_type = "ipo"
    elif "price_move" in match.fin_categories:
        event_type = "price_move"
    elif "sec_event" in match.fin_categories:
        event_type = "sec_filing"
    elif "macro" in match.fin_categories:
        event_type = "macro"
    elif "commodities" in match.fin_categories:
        event_type = "commodities"
    elif "corporate" in match.fin_categories:
        event_type = "corporate"
    else:
        event_type = "general"

    return {
        "urgency": urgency,
        "event_type": event_type,
        "sentiment": sent,
    }
