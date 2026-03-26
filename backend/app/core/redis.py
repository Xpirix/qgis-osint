from __future__ import annotations
import json
from typing import AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis():
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# ── Cache helpers ──────────────────────────────────────────────────────────────

async def cache_get(key: str) -> str | None:
    r = await get_redis()
    return await r.get(key)


async def cache_set(key: str, value: str, ttl: int | None = None):
    r = await get_redis()
    if ttl:
        await r.setex(key, ttl, value)
    else:
        await r.set(key, value)


async def cache_get_json(key: str) -> dict | list | None:
    raw = await cache_get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set_json(key: str, value: dict | list, ttl: int | None = None):
    await cache_set(key, json.dumps(value, default=str), ttl)


# ── Pub/Sub helpers ────────────────────────────────────────────────────────────

SSE_CHANNEL = "sse:broadcast"


async def publish_sse(event_type: str, data: dict):
    r = await get_redis()
    payload = json.dumps({"event": event_type, "data": data}, default=str)
    await r.publish(SSE_CHANNEL, payload)


async def subscribe_sse() -> AsyncGenerator[tuple[str, dict], None]:
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(SSE_CHANNEL)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                payload = json.loads(message["data"])
                yield payload["event"], payload["data"]
    finally:
        await pubsub.unsubscribe(SSE_CHANNEL)
        await pubsub.aclose()
