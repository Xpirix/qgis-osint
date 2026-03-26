"""Feed item endpoints — data served from Redis cache."""
from __future__ import annotations
import json
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.core.redis import cache_get_json

router = APIRouter()
log = logging.getLogger(__name__)

VALID_CHANNELS = {
    "commits", "news", "blog", "planet", "plugins",
    "hub", "qeps", "changelog", "mailing_dev", "mailing_user",
}


@router.get("/{name}", summary="Latest feed items for a named channel")
async def get_feed(
    name: str,
    limit: int = Query(default=20, ge=1, le=100),
    repo: str | None = Query(default=None),
):
    if name not in VALID_CHANNELS:
        raise HTTPException(status_code=404, detail=f"Feed '{name}' not found")

    items = await cache_get_json(f"feed:{name}") or []

    if repo and name == "commits":
        items = [i for i in items if i.get("repo") == repo]

    return JSONResponse(content=items[:limit])
