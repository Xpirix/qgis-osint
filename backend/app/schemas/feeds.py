from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FeedItemResponse(BaseModel):
    id: str
    channel: str
    repo: Optional[str] = None
    title: str
    meta: str
    tag: str
    color: str
    url: str
    timestamp: str

    model_config = {"from_attributes": True}
