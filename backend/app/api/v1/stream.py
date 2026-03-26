"""Server-Sent Events endpoint — streams live events to browsers via Redis pub/sub."""
from __future__ import annotations
import asyncio
import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.core.redis import get_redis, SSE_CHANNEL

router = APIRouter()
log = logging.getLogger(__name__)


async def _event_generator(request: Request):
    """Yield SSE-formatted strings from the Redis pub/sub channel."""
    yield "retry: 3000\n\n"  # Tell browser to reconnect after 3s

    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(SSE_CHANNEL)

    try:
        async for message in pubsub.listen():
            if await request.is_disconnected():
                break
            if message["type"] != "message":
                continue
            try:
                payload = json.loads(message["data"])
                envelope = json.dumps(
                    {"type": payload.get("event", "message"), "payload": payload.get("data", {})},
                    default=str,
                )
                yield f"data: {envelope}\n\n"
            except (json.JSONDecodeError, KeyError) as exc:
                log.debug("SSE parse error: %s", exc)
    except asyncio.CancelledError:
        pass
    finally:
        try:
            await pubsub.unsubscribe(SSE_CHANNEL)
            await pubsub.aclose()
        except Exception:
            pass


@router.get("", summary="Server-Sent Events stream")
async def sse_stream(request: Request):
    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
