"""
Keyword matching for financial and geopolitical events.
Returns (matched, category, tickers_mentioned) without hitting any API.
"""
import re
from dataclasses import dataclass, field

# ── Geopolitical conflict zones & actors ─────────────────────────────────────
GEO_PATTERNS: dict[str, list[str]] = {
    "middle_east": [
        r"\biran\b", r"\bisrael\b", r"\bhezbollah\b", r"\bhamas\b",
        r"\bgaza\b", r"\bwest bank\b", r"\beiran.israel\b", r"\bstrait of hormuz\b",
        r"\bpersia[n]?\b", r"\bahmadinejad\b", r"\bkhamenei\b", r"\bnetanyahu\b",
        r"\bidf\b", r"\birgc\b", r"\bproxy war\b", r"\bbeirut\b", r"\bsyria\b",
        r"\byemen\b", r"\bhouthi\b", r"\bred sea\b", r"\bsuez\b",
    ],
    "eastern_europe": [
        r"\brussia\b", r"\bukraine\b", r"\bputin\b", r"\bzelensky\b",
        r"\bkremlin\b", r"\bdonbas\b", r"\bkharkiv\b", r"\bblack sea\b",
        r"\bnato\b", r"\bsanctions\b", r"\bnord stream\b", r"\bnatural gas\b.*\brussia\b",
        r"\bbalt[a-z]+\b.*\bwar\b",
    ],
    "asia_pacific": [
        r"\btaiwan\b", r"\btaiwan strait\b", r"\bchina.taiwan\b", r"\bpla\b",
        r"\bnorth korea\b", r"\bkim jong\b", r"\bnuclear test\b",
        r"\bsouth china sea\b", r"\bindopacific\b", r"\bsemiconductor.*ban\b",
        r"\bchip.*export.*control\b",
    ],
    "global_conflict": [
        r"\bwar\b", r"\bmissile strike\b", r"\bdrone attack\b", r"\bblockade\b",
        r"\bcoup\b", r"\bterror attack\b", r"\bexplosion.*port\b",
        r"\bshipping.*disruption\b", r"\btanker.*seized\b",
    ],
}

# ── Financial market events ───────────────────────────────────────────────────
FIN_PATTERNS: dict[str, list[str]] = {
    "ipo": [
        r"\bipo\b", r"\binitial public offer\b", r"\bs-1\b", r"\bprospectus\b",
        r"\bdebut.*trading\b", r"\blist.*stock exchange\b", r"\bdirect listing\b",
        r"\bspac\b",
    ],
    "price_move": [
        r"\bsurge[sd]?\b", r"\bplunge[sd]?\b", r"\bcrash\b", r"\bsoar\b",
        r"\bfree.?fall\b", r"\b(up|down)\s+\d+%\b", r"\b52.week\s+(high|low)\b",
        r"\bcircuit breaker\b", r"\bhalted\b",
    ],
    "macro": [
        r"\bfed\b.*\brate\b", r"\binterest rate\b", r"\bfomc\b", r"\binflation\b",
        r"\bcpi\b", r"\bpce\b", r"\brecession\b", r"\bgdp\b", r"\byield curve\b",
        r"\bbond yield\b", r"\bdollar index\b", r"\bdxy\b",
    ],
    "corporate": [
        r"\bearnings\b", r"\beps\b", r"\bbeat\b.*\bestimate\b", r"\bmiss\b.*\bestimate\b",
        r"\bacquisition\b", r"\bmerger\b", r"\bbankruptcy\b", r"\bchapter 11\b",
        r"\blayoff\b", r"\brestructur\b", r"\bdividend\b", r"\bbuyback\b",
    ],
    "sec_event": [
        r"\b8-k\b", r"\b10-k\b", r"\b10-q\b", r"\binsider\s+(buy|sell)\b",
        r"\bsec\s+filing\b", r"\bwhistleblower\b", r"\bfraud\b", r"\bsec\s+charge\b",
    ],
    "commodities": [
        r"\bcrude oil\b", r"\bwti\b", r"\bbrent\b", r"\bopec\b", r"\bnatural gas\b",
        r"\bgold\s+price\b", r"\bxau\b", r"\bsilver\b", r"\bcopper\b",
        r"\bwheat\b", r"\bcorn\b", r"\bsoybeans\b",
    ],
    "crypto": [
        r"\bbitcoin\b", r"\bethereun\b", r"\bcrypto\b", r"\bstablecoin\b",
        r"\bsec.*crypto\b", r"\betf.*bitcoin\b", r"\bdefi\b",
    ],
}

# ── Instruments directly impacted by geopolitical events ─────────────────────
GEO_INSTRUMENT_MAP: dict[str, list[str]] = {
    "middle_east": ["CL=F", "BZ=F", "GC=F", "USO", "XLE", "LMT", "RTX", "NOC"],
    "eastern_europe": ["CL=F", "NG=F", "GC=F", "EURUSD=X", "RUB=X", "TTF"],
    "asia_pacific":  ["TSM", "NVDA", "AMAT", "SOXX", "JPY=X", "USDJPY=X"],
    "global_conflict": ["GC=F", "SI=F", "CL=F", "TLT", "VIX"],
}

# ── Precompile all patterns ───────────────────────────────────────────────────
_GEO_COMPILED = {
    cat: [re.compile(p, re.IGNORECASE) for p in pats]
    for cat, pats in GEO_PATTERNS.items()
}
_FIN_COMPILED = {
    cat: [re.compile(p, re.IGNORECASE) for p in pats]
    for cat, pats in FIN_PATTERNS.items()
}

# Ticker extraction: $AAPL or standalone 1-5 uppercase letter words
_TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b|(?<!\w)([A-Z]{1,5})(?!\w)(?=\s)")


@dataclass
class MatchResult:
    matched: bool
    geo_categories: list[str] = field(default_factory=list)
    fin_categories: list[str] = field(default_factory=list)
    implied_instruments: list[str] = field(default_factory=list)
    tickers_mentioned: list[str] = field(default_factory=list)


def match(text: str) -> MatchResult:
    geo_hits, fin_hits = [], []

    for cat, patterns in _GEO_COMPILED.items():
        if any(p.search(text) for p in patterns):
            geo_hits.append(cat)

    for cat, patterns in _FIN_COMPILED.items():
        if any(p.search(text) for p in patterns):
            fin_hits.append(cat)

    instruments: list[str] = []
    for cat in geo_hits:
        instruments.extend(GEO_INSTRUMENT_MAP.get(cat, []))

    tickers = list({m.group(1) or m.group(2) for m in _TICKER_RE.finditer(text) if (m.group(1) or m.group(2))})

    matched = bool(geo_hits or fin_hits)
    return MatchResult(
        matched=matched,
        geo_categories=geo_hits,
        fin_categories=fin_hits,
        implied_instruments=list(dict.fromkeys(instruments)),
        tickers_mentioned=tickers,
    )
