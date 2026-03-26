"""GeoJSON layer endpoint.

Dynamic layers (user_groups, members, events) are served from Redis where the
scraper worker writes fresh GeoJSON FeatureCollections. The proxy layers
(contributors, supporting contributors) are served from the proxy cache that
the layers worker refreshes from qgis.org.

Static layers (mirrors, certified_trainers, organisations) are served from
PostGIS — those are seeded manually via `python -m app.cli seed`.
"""
from __future__ import annotations
import json
import logging
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.core.redis import cache_get_json
from app.models.spatial import LayerFeature

router = APIRouter()
log = logging.getLogger(__name__)

# Layers served from Redis by the scraper worker (dynamic, no PostgreSQL)
_REDIS_LAYERS = {"user_groups", "members", "events"}

LayerName = Literal[
    "user_groups", "members", "events", "mirrors",
    "certified_trainers", "organisations"
]

LAYER_COLOURS = {
    "user_groups": "#589632",
    "members": "#ee7913",
    "events": "#e05c5c",
    "mirrors": "#c8d8e8",
    "certified_trainers": "#a8c4e0",
    "organisations": "#7ecba1",
}


@router.get("/{name}", summary="GeoJSON for a processed spatial layer")
async def get_layer(name: str, db: AsyncSession = Depends(get_db)):
    if name not in LAYER_COLOURS:
        raise HTTPException(status_code=404, detail=f"Layer '{name}' not found")

    # Dynamic layers: served from Redis (written by scraper worker)
    if name in _REDIS_LAYERS:
        fc = await cache_get_json(f"layer:{name}")
        if fc is None:
            # Return empty FeatureCollection if scraper hasn't run yet
            fc = {"type": "FeatureCollection", "features": []}
            log.warning("Layer %s not yet in Redis — returning empty collection", name)
        return Response(content=json.dumps(fc), media_type="application/json")

    # Static layers: served from PostGIS
    result = await db.execute(
        select(LayerFeature).where(LayerFeature.layer == name)
    )
    features_db = result.scalars().all()

    features = []
    for feat in features_db:
        props = {**feat.properties, "layer": name, "colour": LAYER_COLOURS[name]}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [feat.longitude, feat.latitude]},
            "properties": props,
        })

    fc = json.dumps({"type": "FeatureCollection", "features": features})
    return Response(content=fc, media_type="application/json")
