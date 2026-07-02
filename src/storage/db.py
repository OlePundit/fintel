"""PostgreSQL models and deduplication via URL + title hash."""
import hashlib
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer,
    String, Text, create_engine, text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    body = Column(Text)
    published_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Analysis results
    matched = Column(Boolean, default=False)
    urgency = Column(Integer)
    event_type = Column(String(50))
    sentiment_compound = Column(Float)
    geo_categories = Column(Text)   # JSON-encoded list
    fin_categories = Column(Text)   # JSON-encoded list
    tickers = Column(Text)          # JSON-encoded list
    instruments = Column(Text)      # JSON-encoded list
    alerted = Column(Boolean, default=False)


def make_hash(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}|{title}".encode()).hexdigest()


def is_duplicate(session: Session, url: str, title: str) -> bool:
    h = make_hash(url, title)
    return session.query(Article.id).filter(Article.hash == h).first() is not None


def save_article(session: Session, data: dict) -> Article | None:
    h = make_hash(data["url"], data["title"])
    if session.query(Article.id).filter(Article.hash == h).first():
        return None
    article = Article(hash=h, **data)
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


def get_pending_digest(session: Session, since: datetime) -> list[Article]:
    return (
        session.query(Article)
        .filter(Article.matched == True, Article.collected_at >= since)
        .order_by(Article.urgency.desc())
        .all()
    )


def init_db():
    Base.metadata.create_all(bind=engine)
