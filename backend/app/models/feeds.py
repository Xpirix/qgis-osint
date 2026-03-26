"""Feed item Pydantic model (not stored in DB — lives in Redis only)."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FeedItem(BaseModel):
    id: str
    channel: str
    repo: Optional[str] = None
    title: str
    meta: str
    tag: str
    color: str
    url: str
    timestamp: str
