"""Reddit collector via PRAW — no OAuth, read-only app credentials."""
import praw
from loguru import logger

from config.settings import settings

SUBREDDITS = [
    "wallstreetbets",
    "investing",
    "StockMarket",
    "options",
    "SecurityAnalysis",
    "geopolitics",
    "worldnews",         # geopolitical events
    "Economics",
]

_reddit: praw.Reddit | None = None


def _get_client() -> praw.Reddit:
    global _reddit
    if _reddit is None:
        _reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
    return _reddit


def collect(limit: int = 25) -> list[dict]:
    if not settings.reddit_client_id:
        logger.warning("Reddit: no credentials configured, skipping")
        return []

    client = _get_client()
    results = []
    for sub_name in SUBREDDITS:
        try:
            sub = client.subreddit(sub_name)
            for post in sub.new(limit=limit):
                results.append({
                    "source": "reddit",
                    "title": post.title,
                    "url": f"https://reddit.com{post.permalink}",
                    "body": post.selftext[:1000] if post.selftext else post.url,
                    "published_at": str(post.created_utc),
                })
            logger.debug(f"Reddit [r/{sub_name}] fetched {limit} posts")
        except Exception as e:
            logger.warning(f"Reddit [r/{sub_name}] failed: {e}")
    return results
