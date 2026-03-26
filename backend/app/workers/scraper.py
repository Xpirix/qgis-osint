"""Dynamic harvester for user groups, sustaining members, and events.

Data flow:
  1. Harvest live data from remote sources.
  2. Write GeoJSON FeatureCollections to Redis (layer:{name}).
  3. Publish layer_update SSE events so browsers refresh immediately.

Sustaining members are stored without map geometry — they are displayed only
in the right-panel list, not on the map.
"""
from __future__ import annotations
import json
import logging
import os
import pathlib
import re
from html.parser import HTMLParser

import httpx

from app.core.redis import cache_get_json, cache_set_json, publish_sse

log = logging.getLogger(__name__)

# -- Source URLs ---------------------------------------------------------------
MEMBERS_JSON_URL = "https://members.qgis.org/en/members/json/"
GROUPS_URL = "https://qgis.org/community/groups/"
WIKI_HOME_URL = "https://github.com/qgis/QGIS/wiki"
HACKFESTS_JSON_URL = "https://raw.githubusercontent.com/qgis/QGIS/master/resources/data/qgis-hackfests.json"
USER_GROUPS_JSON_URL = "https://raw.githubusercontent.com/qgis/QGIS/master/resources/data/user_groups_data.json"

# -- Data directory ------------------------------------------------------------
_DATA_DIR = pathlib.Path(
    os.getenv("DATA_DIR", str(pathlib.Path(__file__).parent.parent.parent.parent / "data"))
)

LAYER_COLOURS = {
    "user_groups": "#589632",
    "events": "#e05c5c",
}

MEMBER_LEVEL_MAP = {
    "Flagship": "flagship",
    "Large": "large",
    "Medium": "medium",
    "Small": "small",
}

# -- Helpers -------------------------------------------------------------------

def _make_geojson(features: list[dict], layer: str) -> dict:
    return {"type": "FeatureCollection", "layer": layer, "features": features}


def _feature(lon: float, lat: float, props: dict, layer: str) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {**props, "layer": layer, "colour": LAYER_COLOURS.get(layer, "#888888")},
    }


# -- Members harvester ---------------------------------------------------------

async def _harvest_members(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(MEMBERS_JSON_URL)
    resp.raise_for_status()
    data = resp.json()
    items_raw = data.get("rss", {}).get("channel", {}).get("item", [])
    features = []
    for m in items_raw:
        slug = (m.get("slug") or "").strip()
        name = (m.get("title") or "").strip()
        country = (m.get("member_country") or "").strip()
        tier = MEMBER_LEVEL_MAP.get(m.get("member_level") or "", "small")
        website = (m.get("member_url") or "").strip()
        logo_url = (m.get("image_url") or "").strip()
        start_date = (m.get("start_date") or "")[:10]
        end_date = (m.get("end_date") or "")[:10]

        features.append({
            "type": "Feature",
            "geometry": None,
            "properties": {
                "name": name,
                "slug": slug,
                "tier": tier,
                "country": country,
                "website": website,
                "logo_url": logo_url,
                "start_date": start_date,
                "end_date": end_date,
            },
        })

    log.info("Members harvested: %d features", len(features))
    return features


# -- User-groups harvester ---------------------------------------------------

async def _harvest_groups(client: httpx.AsyncClient) -> list[dict]:
    """Fetch user groups from GitHub JSON and join with country polygon file."""
    resp = await client.get(USER_GROUPS_JSON_URL)
    resp.raise_for_status()

    # Load country polygons from local file
    poly_path = _DATA_DIR / "countries_polygon.geojson"
    try:
        with poly_path.open(encoding="utf-8") as fh:
            countries_fc = json.load(fh)
    except Exception as exc:
        log.warning("Cannot load countries_polygon.geojson: %s", exc)
        countries_fc = {"features": []}

    # Build iso_a2 → (geometry, display name) index
    country_geoms: dict[str, tuple[dict, str]] = {}
    for feat in countries_fc.get("features", []):
        iso = (feat.get("properties", {}).get("iso_a2") or "").strip().upper()
        cname = feat.get("properties", {}).get("NAME", "")
        geom = feat.get("geometry")
        if iso and geom:
            country_geoms[iso] = (geom, cname)

    fc = resp.json()
    features = []
    colour = LAYER_COLOURS.get("user_groups", "#38bdf8")

    for feat in fc.get("features", []):
        props = feat.get("properties") or {}
        iso2 = (props.get("country") or "").strip().upper()
        name = (props.get("name") or "").strip()
        website = (props.get("website") or "").strip()
        logo_url = (props.get("logo_url") or "").strip()
        year = props.get("year")

        if not iso2 or iso2 not in country_geoms:
            log.debug("No polygon for user group %r (country=%s), skipping", name, iso2)
            continue

        geom, country_name = country_geoms[iso2]
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "name": name,
                "country": iso2,
                "country_name": country_name,
                "website": website,
                "logo_url": logo_url,
                "year": year,
                "layer": "user_groups",
                "colour": colour,
            },
        })

    log.info("User groups harvested: %d polygon features", len(features))
    return features


# -- Events harvester (GitHub wiki) --------------------------------------------

_EVENT_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>(.*?)</td>"
    r"\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>",
    re.DOTALL,
)
_LINK_RE = re.compile(r'href="(https://github\.com/qgis/QGIS/wiki/[^"#]+)"')
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(s: str) -> str:
    return _TAG_RE.sub("", s).strip()


async def _harvest_events(client: httpx.AsyncClient) -> list[dict]:
    """Fetch contributor meetings from the official qgis-hackfests.json GeoJSON."""
    resp = await client.get(HACKFESTS_JSON_URL)
    resp.raise_for_status()

    fc = resp.json()
    features = []

    for feat in fc.get("features", []):
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords or len(coords) < 2:
            continue
        lon, lat = coords[0], coords[1]

        props = feat.get("properties") or {}
        number = props.get("hackfest_number", "")
        place = props.get("place", "")
        date_nice = props.get("date_nice", "")
        notes = props.get("notes", "")

        name = f"QGIS Hackfest #{number} \u2014 {place}" if number else f"QGIS Hackfest \u2014 {place}"

        features.append(_feature(lon, lat, {
            "name": name,
            "event_type": "HACKFEST",
            "date": date_nice,
            "city": place,
            "url": "",
            "notes": notes,
        }, "events"))

    log.info("Hackfests harvested: %d features", len(features))
    return features


# -- Main entry point ----------------------------------------------------------

async def scrape_all():
    log.info("Scraper worker running...")

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "QGIS-Universe/1.0 (https://qgis.org)"},
    ) as client:
        try:
            member_features = await _harvest_members(client)
        except Exception as exc:
            log.warning("Members harvest failed: %s", exc)
            member_features = []

        try:
            group_features = await _harvest_groups(client)
        except Exception as exc:
            log.warning("Groups harvest failed: %s", exc)
            group_features = []

        try:
            event_features = await _harvest_events(client)
        except Exception as exc:
            log.warning("Events harvest failed: %s", exc)
            event_features = []

    TTL = 7 * 24 * 3600  # 7 days

    for layer, features in [
        ("members", member_features),
        ("user_groups", group_features),
        ("events", event_features),
    ]:
        if not features:
            log.warning("No features for layer %s — skipping Redis write", layer)
            continue
        fc = _make_geojson(features, layer)
        await cache_set_json(f"layer:{layer}", fc, ttl=TTL)
        await publish_sse("layer_update", {"layer": layer, "count": len(features)})
        log.info("Layer %s written to Redis: %d features", layer, len(features))

    # Update stats counts
    stats = await cache_get_json("stats:latest") or {}
    updated = False
    if member_features:
        stats["sustaining_members"] = len(member_features)
        updated = True
    if group_features:
        stats["user_groups"] = len(group_features)
        updated = True
    if updated:
        await cache_set_json("stats:latest", stats, ttl=600)
        await publish_sse("stats_update", stats)

    log.info("Scraper worker done")
