"""Initial schema — recommendations and leads tables.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("current_car", sa.String(length=200), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=True),
        sa.Column("budget_range", sa.String(length=20), nullable=False),
        sa.Column("car_type", sa.String(length=10), nullable=False),
        sa.Column("monthly_km", sa.Integer(), nullable=True),
        sa.Column("driving_style", sa.String(length=20), nullable=True),
        sa.Column("can_charge_at_home", sa.Boolean(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendations_id", "recommendations", ["id"], unique=False)
    op.create_index(
        "ix_recommendations_session_id", "recommendations", ["session_id"], unique=True
    )

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("whatsapp", sa.String(length=20), nullable=False),
        sa.Column("current_car", sa.String(length=200), nullable=False),
        sa.Column("budget_clp", sa.BigInteger(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("buy_timeframe", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_id", "leads", ["id"], unique=False)
    op.create_index("ix_leads_session_id", "leads", ["session_id"], unique=False)


def downgrade() -> None:
    """Drop initial tables."""
    op.drop_index("ix_leads_session_id", table_name="leads")
    op.drop_index("ix_leads_id", table_name="leads")
    op.drop_table("leads")
    op.drop_index("ix_recommendations_session_id", table_name="recommendations")
    op.drop_index("ix_recommendations_id", table_name="recommendations")
    op.drop_table("recommendations")
