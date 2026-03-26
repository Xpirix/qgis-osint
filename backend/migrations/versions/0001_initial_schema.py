"""Initial schema — layer_features and stats_snapshots tables.

Revision ID: 0001
Revises:
Create Date: 2026-03-20
"""
from __future__ import annotations
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "layer_features",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("layer", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_layer_features_layer", "layer_features", ["layer"])

    op.create_table(
        "stats_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("stats", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stats_snapshots_generated_at", "stats_snapshots", ["generated_at"])


def downgrade() -> None:
    op.drop_index("ix_stats_snapshots_generated_at", table_name="stats_snapshots")
    op.drop_table("stats_snapshots")
    op.drop_index("ix_layer_features_layer", table_name="layer_features")
    op.drop_table("layer_features")
