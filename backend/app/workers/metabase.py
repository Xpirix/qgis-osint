"""Metabase public dashboard stats worker.

Fetches aggregate statistics from the three public QGIS Metabase instances:
  - plugins.qgis.org/metabase  — plugin counts, total downloads
  - feed.qgis.org/metabase     — active QGIS usage (opens/day)
  - hub.qgis.org/metabase      — hub resource counts by type

All dashboards are publicly accessible (no auth token required).
Cards are identified by (dashcard_id, card_id) — both come from the dashboard
metadata and are stable as long as no one restructures the dashboard.
"""
from __future__ import annotations
import asyncio
import logging
import httpx
from app.core.redis import cache_get_json, cache_set_json, publish_sse

log = logging.getLogger(__name__)

# ── Dashboard coordinates ──────────────────────────────────────────────────────
_PLUGINS_BASE  = "https://plugins.qgis.org/metabase"
_PLUGINS_TOKEN = "7ecd345f-7321-423d-9844-71e526a454a9"

_FEED_BASE  = "https://feed.qgis.org/metabase"
_FEED_TOKEN = "df81071d-4c75-45b8-a698-97b8649d7228"

_HUB_BASE  = "https://hub.qgis.org/metabase"
_HUB_TOKEN = "7ecd345f-7321-423d-9844-71e526a454a9"

# (dashcard_id, card_id, description)
_CARDS = {
    # plugins.qgis.org
    "plugin_count_series":    (_PLUGINS_BASE, _PLUGINS_TOKEN, 61,  60),  # smartscalar cumulative by year
    "plugin_downloads_total": (_PLUGINS_BASE, _PLUGINS_TOKEN, 62,  61),  # scalar: all-time downloads
    # feed.qgis.org
    "qgis_opens_30d":         (_FEED_BASE,    _FEED_TOKEN,    14,  14),  # scalar: opens last 30 days
    "qgis_opens_yesterday":   (_FEED_BASE,    _FEED_TOKEN,    18,  18),  # scalar: opens yesterday
    # hub.qgis.org
    "hub_styles":             (_HUB_BASE,     _HUB_TOKEN,     98,  21),  # scalar: published styles
    "hub_models":             (_HUB_BASE,     _HUB_TOKEN,     97,  23),  # scalar: published models
    "hub_geopackages":        (_HUB_BASE,     _HUB_TOKEN,     96,  24),  # scalar: published geopackages
    "hub_3d_objects":         (_HUB_BASE,     _HUB_TOKEN,     95,  22),  # scalar: published 3D objects
}


async def _fetch_card(
    client: httpx.AsyncClient,
    base: str,
    token: str,
    dashcard_id: int,
    card_id: int,
) -> list:
    """Return the rows list from a Metabase public dashboard card."""
    url = f"{base}/api/public/dashboard/{token}/dashcard/{dashcard_id}/card/{card_id}"
    try:
        r = await client.get(url, timeout=15.0)
        r.raise_for_status()
        return r.json().get("data", {}).get("rows", [])
    except Exception as exc:
        log.warning("Metabase card %s/%s failed: %s", dashcard_id, card_id, exc)
        return []


async def fetch_stats() -> None:
    log.info("Metabase worker running...")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        keys = list(_CARDS.keys())
        rows_list = await asyncio.gather(*[
            _fetch_card(client, base, token, dc, c)
            for base, token, dc, c in _CARDS.values()
        ])

    raw: dict[str, list] = dict(zip(keys, rows_list))

    def scalar(key: str) -> int | None:
        rows = raw.get(key, [])
        return int(rows[0][0]) if rows else None

    # Plugin count: smartscalar returns cumulative-by-year time series; last row = current total
    plugin_count_rows = raw.get("plugin_count_series", [])
    plugin_count = int(plugin_count_rows[-1][1]) if plugin_count_rows else None

    plugin_downloads_total = scalar("plugin_downloads_total")
    qgis_opens_30d         = scalar("qgis_opens_30d")
    qgis_opens_yesterday   = scalar("qgis_opens_yesterday")
    hub_styles             = scalar("hub_styles")
    hub_models             = scalar("hub_models")
    hub_geopackages        = scalar("hub_geopackages")
    hub_3d_objects         = scalar("hub_3d_objects")

    update: dict = {}
    for field, value in [
        ("plugin_count",           plugin_count),
        ("plugin_downloads_total", plugin_downloads_total),
        ("qgis_opens_30d",         qgis_opens_30d),
        ("qgis_opens_yesterday",   qgis_opens_yesterday),
        ("hub_styles",             hub_styles),
        ("hub_models",             hub_models),
        ("hub_geopackages",        hub_geopackages),
        ("hub_3d_objects",         hub_3d_objects),
    ]:
        if value is not None:
            update[field] = value

    # Total hub resources as typed sum (more accurate than the REST count endpoint)
    hub_total = sum(
        v for v in [hub_styles, hub_models, hub_geopackages, hub_3d_objects]
        if v is not None
    )
    if hub_total:
        update["hub_resources"] = hub_total

    if update:
        stats = await cache_get_json("stats:latest") or {}
        stats.update(update)
        await cache_set_json("stats:latest", stats, ttl=7200)
        await publish_sse("stats_update", stats)

    log.info(
        "Metabase worker done: plugins=%s total_dl=%s opens_30d=%s opens_yd=%s hub=%s",
        plugin_count,
        plugin_downloads_total,
        qgis_opens_30d,
        qgis_opens_yesterday,
        update.get("hub_resources"),
    )
