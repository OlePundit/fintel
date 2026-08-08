"""Celery app + Beat schedule."""
from celery import Celery
from celery.schedules import crontab

from config.settings import settings

app = Celery("fintel", broker=settings.redis_url, backend=settings.redis_url)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

app.conf.beat_schedule = {
    # Main news pipeline — every 15 minutes
    "collect-rss": {
        "task": "src.tasks.pipeline.run_rss",
        "schedule": 900,
    },
    # GDELT geopolitical — every 30 minutes (1h timespan query)
    "collect-gdelt": {
        "task": "src.tasks.pipeline.run_gdelt",
        "schedule": 1800,
    },
    # EDGAR filings — every hour
    "collect-edgar": {
        "task": "src.tasks.pipeline.run_edgar",
        "schedule": 3600,
    },
    # Reddit — every 20 minutes
    "collect-reddit": {
        "task": "src.tasks.pipeline.run_reddit",
        "schedule": 1200,
    },
    # StockTwits — every 10 minutes
    "collect-stocktwits": {
        "task": "src.tasks.pipeline.run_stocktwits",
        "schedule": 600,
    },
    # Daily email digest at 07:00 UTC
    "daily-digest": {
        "task": "src.tasks.pipeline.send_daily_digest",
        "schedule": crontab(hour=7, minute=0),
    },
}

# autodiscover_tasks looks for a `tasks` submodule per package; our tasks
# live in `pipeline.py`, so import it directly to register them.
app.conf.imports = ("src.tasks.pipeline",)
