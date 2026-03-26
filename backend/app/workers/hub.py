"""hub.qgis.org API worker."""
from __future__ import annotations
import logging
import httpx
from app.core.redis import cache_get_json, cache_set_json, publish_sse

log = logging.getLogger(__name__)

HUB_API = "https://hub.qgis.org/api/v1/resources/?limit=20"
HUB_COUNT_API = "https://hub.qgis.org/api/v1/resources/?limit=1"


async def fetch_hub():
    log.info("Hub worker running...")
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(HUB_API)
            resp.raise_for_status()
            data = resp.json()

            count_resp = await client.get(HUB_COUNT_API)
            count_resp.raise_for_status()
            count_data = count_resp.json()

        total = count_data.get("total", count_data.get("count", 0))
        results = data.get("results", data if isinstance(data, list) else [])

        items = []
        for resource in results[:20]:
            name = resource.get("name", resource.get("title", ""))[:100]
            creator = resource.get("creator", resource.get("owner", ""))
            rtype = resource.get("resource_type", resource.get("type", "RESOURCE"))
            upload_date = resource.get("upload_date", resource.get("date", ""))[:10]
            dl_count = resource.get("download_count", resource.get("downloads", 0))
            res_uuid = resource.get("uuid", resource.get("id", ""))

            items.append({
                "id": f"hub:{res_uuid}",
                "channel": "hub",
                "title": f"{name}",
                "meta": f"{creator} · {rtype} · {upload_date}",
                "tag": str(rtype).upper()[:8],
                "color": "#7ecba1",
                "url": f"https://hub.qgis.org/geopackages/{res_uuid}/" if res_uuid else "https://hub.qgis.org",
                "timestamp": resource.get("upload_date", resource.get("date", "")),
            })

        await cache_set_json("feed:hub", items, ttl=1800)

        stats = await cache_get_json("stats:latest") or {}
        stats["hub_resources"] = total
        await cache_set_json("stats:latest", stats, ttl=600)
        await publish_sse("stats_update", stats)

        if items:
            await publish_sse("feed_item", items[0])

    except Exception as exc:
        log.warning("Hub worker failed: %s", exc)

    log.info("Hub worker done")
