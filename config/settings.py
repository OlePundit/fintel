from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "fintel"
    postgres_user: str = "fintel"
    postgres_password: str = "changeme"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "fintel-bot/1.0"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Mailtrap SMTP
    mail_host: str = "live.smtp.mailtrap.io"
    mail_port: int = 587
    mail_username: str = "api"
    mail_password: str = ""
    mail_from_address: str = ""
    mail_from_name: str = "Fintel Bot"
    digest_to_email: str = ""

    # Pipeline
    min_alert_urgency: int = 3
    max_articles_per_run: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # silently drop unknown env vars like MAIL_MAILER, MAIL_ENCRYPTION
    )


settings = Settings()
