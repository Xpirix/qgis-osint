"""Cached transparent proxy for contributor GeoJSON files from qgis.org."""
from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import httpx
from app.core.config import settings
from app.core.redis import cache_get, cache_set

router = APIRouter()
log = logging.getLogger(__name__)

ALLOWED_FILES = {"contributors_map.json", "supporting_map.json"}
UPSTREAM_BASE = "https://www.qgis.org/data/contributors"
FALLBACK_CDN = "https://raw.githubusercontent.com/qgis/QGIS-Website/main/static/data/contributors"


@router.get("/{filename}", summary="Proxy contributor GeoJSON from qgis.org")
async def proxy_geojson(filename: str):
    if filename not in ALLOWED_FILES:
        raise HTTPException(status_code=404, detail="File not found")

    cache_key = f"proxy:{filename}"
    cached = await cache_get(cache_key)
    if cached:
        return Response(content=cached, media_type="application/json")

    # Try primary upstream then fallback CDN
    for url in [f"{UPSTREAM_BASE}/{filename}", f"{FALLBACK_CDN}/{filename}"]:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url)
            if resp.status_code == 200:
                body = resp.text
                await cache_set(cache_key, body, ttl=settings.proxy_cache_ttl)
                return Response(content=body, media_type="application/json")
        except Exception as exc:
            log.warning("Proxy fetch failed for %s: %s", url, exc)

    raise HTTPException(status_code=502, detail="Upstream unavailable")
