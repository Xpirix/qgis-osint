"""Analytics worker — Matomo public API, Metabase, and version.qgis.org."""
from __future__ import annotations
import logging
import httpx
from app.core.redis import cache_get_json, cache_set_json, publish_sse

log = logging.getLogger(__name__)

MATOMO_API = (
    "https://matomo.qgis.org/index.php"
    "?module=API&method=UserCountry.getCountry"
    "&period=month&date=today&format=JSON"
    "&token_auth=anonymous&idSite=1"
)

VERSION_URL = "https://version.qgis.org/version.json"


async def _fetch_version() -> dict:
    """Fetch latest/LTR QGIS version from version.qgis.org."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(VERSION_URL)
            resp.raise_for_status()
            data = resp.json()
        latest = data.get("latest", {})
        ltr    = data.get("ltr", {})
        result = {
            "latest_release":      latest.get("version", ""),
            "latest_release_name": latest.get("name", ""),
            "ltr_release":         ltr.get("version", ""),
            "ltr_release_name":    ltr.get("name", ""),
            "latest_release_date": latest.get("date", ""),
        }
        log.info("Version: latest=%s, LTR=%s", result["latest_release"], result["ltr_release"])
        return result
    except Exception as exc:
        log.warning("Version fetch failed: %s", exc)
        return {}


async def fetch_analytics():
    log.info("Analytics worker running...")

    # Fetch QGIS version
    version_data = await _fetch_version()
    if version_data:
        stats = await cache_get_json("stats:latest") or {}
        stats.update(version_data)
        await cache_set_json("stats:latest", stats, ttl=86400)
        await publish_sse("stats_update", stats)
        await cache_set_json("version:latest", version_data, ttl=3600)

    # Fetch Matomo analytics
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(MATOMO_API)
            if resp.status_code == 200:
                data = resp.json()
                await cache_set_json("analytics:country", data, ttl=86400)
                log.info("Analytics: got %d countries", len(data) if isinstance(data, list) else 0)
    except Exception as exc:
        log.warning("Analytics (Matomo) worker failed: %s", exc)

    log.info("Analytics worker done")

