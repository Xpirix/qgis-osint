"""GeoJSON proxy refresh worker — pre-warms contributor layer caches."""
from __future__ import annotations
import logging
import httpx
from app.core.config import settings
from app.core.redis import cache_set, publish_sse

log = logging.getLogger(__name__)

FILES = ["contributors_map.json", "supporting_map.json"]
UPSTREAM_BASE = "https://www.qgis.org/data/contributors"
FALLBACK_CDN = "https://raw.githubusercontent.com/qgis/QGIS-Website/main/static/data/contributors"


async def refresh_proxy_layers():
    log.info("Proxy layer refresh worker running...")
    for filename in FILES:
        success = False
        for base_url in [UPSTREAM_BASE, FALLBACK_CDN]:
            url = f"{base_url}/{filename}"
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(url)
                if resp.status_code == 200:
                    await cache_set(f"proxy:{filename}", resp.text, ttl=settings.proxy_cache_ttl)
                    log.info("Refreshed proxy cache for %s (%d bytes)", filename, len(resp.text))
                    await publish_sse("layer_update", {"layer": filename.replace(".json", "")})
                    success = True

                    # Update contributor count stat from contributors_map.json
                    if filename == "contributors_map.json":
                        import json
                        try:
                            fc = json.loads(resp.text)
                            count = len(fc.get("features", []))
                            from app.core.redis import cache_get_json, cache_set_json
                            stats = await cache_get_json("stats:latest") or {}
                            stats["contributors_geo_located"] = count
                            await cache_set_json("stats:latest", stats, ttl=600)
                            await publish_sse("stats_update", stats)
                        except Exception:
                            pass
                    break
            except Exception as exc:
                log.warning("Proxy refresh failed for %s at %s: %s", filename, url, exc)

        if not success:
            log.error("Failed to refresh proxy layer for %s from all upstreams", filename)

    log.info("Proxy layer refresh done")
