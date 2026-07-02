"""Initial articles table

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hash", sa.String(64), unique=True, nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("matched", sa.Boolean(), default=False),
        sa.Column("urgency", sa.Integer()),
        sa.Column("event_type", sa.String(50)),
        sa.Column("sentiment_compound", sa.Float()),
        sa.Column("geo_categories", sa.Text()),
        sa.Column("fin_categories", sa.Text()),
        sa.Column("tickers", sa.Text()),
        sa.Column("instruments", sa.Text()),
        sa.Column("alerted", sa.Boolean(), default=False),
    )
    op.create_index("ix_articles_hash", "articles", ["hash"])
    op.create_index("ix_articles_urgency", "articles", ["urgency"])
    op.create_index("ix_articles_collected_at", "articles", ["collected_at"])


def downgrade():
    op.drop_table("articles")
