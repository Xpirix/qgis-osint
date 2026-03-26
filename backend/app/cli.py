"""CLI management commands.

Usage:
    python -m app.cli refresh-feeds  # Force immediate refresh of all feed workers
    python -m app.cli refresh-layers # Re-proxy contributor GeoJSON files
"""
from __future__ import annotations
import asyncio
import logging

import typer

app = typer.Typer(help="QGIS OSINT Matrix management commands")
log = logging.getLogger(__name__)
logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")


async def _do_refresh_feeds():
    from app.workers import github, rss, plugins, hub, analytics, scraper
    log.info("Refreshing all feed workers...")
    await asyncio.gather(
        github.fetch_all(),
        rss.fetch_all(),
        plugins.fetch_plugins(),
        hub.fetch_hub(),
        analytics.fetch_analytics(),
        scraper.scrape_all(),
    )
    log.info("All feeds refreshed.")


async def _do_refresh_layers():
    from app.workers.layers import refresh_proxy_layers
    log.info("Refreshing proxy layers...")
    await refresh_proxy_layers()
    log.info("Proxy layers refreshed.")


# ── CLI commands ──────────────────────────────────────────────────────────────

@app.command(name="refresh-feeds")
def refresh_feeds():
    """Force immediate refresh of all feed workers."""
    asyncio.run(_do_refresh_feeds())


@app.command(name="refresh-layers")
def refresh_layers():
    """Force re-proxy of contributor GeoJSON files."""
    asyncio.run(_do_refresh_layers())


if __name__ == "__main__":
    app()
