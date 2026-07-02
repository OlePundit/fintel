"""VADER sentiment scoring with financial-domain booster words."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

# Supplement VADER's lexicon with financial terms it under-weights
_FINANCIAL_LEXICON = {
    "bankruptcy": -3.5, "default": -2.5, "downgrade": -2.0, "recall": -1.5,
    "investigation": -1.5, "fraud": -3.0, "lawsuit": -1.8, "layoffs": -2.0,
    "restructuring": -1.5, "delisted": -3.0, "miss": -1.5, "plunge": -2.8,
    "crash": -3.0, "tumble": -2.0, "selloff": -2.2, "capitulation": -2.5,
    "ipo": 1.5, "acquisition": 1.2, "buyback": 1.5, "dividend": 1.2,
    "beat": 1.8, "surge": 2.0, "soar": 2.2, "record": 1.2, "bullish": 1.8,
    "upgrade": 1.8, "outperform": 1.5, "rally": 1.8, "breakout": 1.5,
    # Geopolitical
    "war": -2.5, "strike": -1.5, "attack": -2.0, "sanctions": -1.8,
    "blockade": -2.0, "escalation": -2.2, "ceasefire": 1.5, "deal": 1.0,
    "agreement": 1.2, "treaty": 1.5,
}

_analyzer.lexicon.update(_FINANCIAL_LEXICON)


def score(text: str) -> dict:
    """
    Returns VADER compound score (-1 to +1) and a human label.
    compound > 0.05  → positive
    compound < -0.05 → negative
    else             → neutral
    """
    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "compound": round(compound, 4),
        "label": label,
        "pos": round(scores["pos"], 3),
        "neg": round(scores["neg"], 3),
        "neu": round(scores["neu"], 3),
    }
