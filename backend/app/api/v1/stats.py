"""Global stats endpoint."""
from __future__ import annotations
import datetime
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.redis import cache_get_json

router = APIRouter()
log = logging.getLogger(__name__)

_DEFAULTS = {
    "contributors_geo_located": 0,
    "contributors_total": 809,
    "user_groups": 38,
    "sustaining_members": 80,
    "contributing_orgs": 20,
    "plugin_count": 0,
    "hub_resources": 0,
    "latest_release": "4.0",
    "latest_release_name": "Norrköping",
    "ltr_release": "3.44",
    "ltr_release_name": "Solothurn",
    "latest_release_date": "2026-03-06",
    "next_release_date": None,
    "github_stars": 0,
    "github_forks": 0,
    "open_issues": 0,
    "open_qeps": 0,
    "top_contributor_login": "nyalldawson",
    "top_contributor_commits": 24845,
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
}


@router.get("", summary="Global dashboard statistics")
async def get_stats():
    cached = await cache_get_json("stats:latest")
    if cached:
        return JSONResponse(content=cached)
    return JSONResponse(content=_DEFAULTS)
