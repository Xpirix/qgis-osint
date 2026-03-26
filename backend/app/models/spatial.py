from __future__ import annotations
import datetime
from sqlalchemy import String, Float, DateTime, JSON, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class LayerFeature(Base):
    """A spatial feature in one of the processed layers (user_groups, members, etc.)."""
    __tablename__ = "layer_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    layer: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    properties: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
