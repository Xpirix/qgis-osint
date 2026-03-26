"""APScheduler job registration and lifecycle."""
from __future__ import annotations
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import settings

log = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def start_scheduler():
    global _scheduler
    # Import workers here to avoid circular imports
    from app.workers import github, rss, plugins, hub, analytics, scraper, layers as layers_worker, metabase

    _scheduler = AsyncIOScheduler(timezone="UTC")

    _scheduler.add_job(
        github.fetch_all,
        IntervalTrigger(seconds=settings.fetch_interval_commits),
        id="github", replace_existing=True, misfire_grace_time=60,
    )
    _scheduler.add_job(
        rss.fetch_all,
        IntervalTrigger(seconds=settings.fetch_interval_rss),
        id="rss", replace_existing=True, misfire_grace_time=60,
    )
    _scheduler.add_job(
        plugins.fetch_plugins,
        IntervalTrigger(seconds=settings.fetch_interval_plugins),
        id="plugins", replace_existing=True, misfire_grace_time=60,
    )
    _scheduler.add_job(
        hub.fetch_hub,
        IntervalTrigger(seconds=settings.fetch_interval_hub),
        id="hub", replace_existing=True, misfire_grace_time=60,
    )
    _scheduler.add_job(
        analytics.fetch_analytics,
        IntervalTrigger(seconds=settings.fetch_interval_analytics),
        id="analytics", replace_existing=True, misfire_grace_time=300,
    )
    _scheduler.add_job(
        metabase.fetch_stats,
        IntervalTrigger(seconds=settings.fetch_interval_metabase),
        id="metabase", replace_existing=True, misfire_grace_time=300,
    )
    _scheduler.add_job(
        scraper.scrape_all,
        IntervalTrigger(seconds=settings.fetch_interval_scrape),
        id="scraper", replace_existing=True, misfire_grace_time=3600,
    )
    _scheduler.add_job(
        layers_worker.refresh_proxy_layers,
        IntervalTrigger(seconds=settings.fetch_interval_layers),
        id="layers", replace_existing=True, misfire_grace_time=300,
    )

    _scheduler.start()

    # Fire all workers immediately on startup as async tasks so the caches are
    # populated before any browser makes its first REST call.  These run in
    # parallel and do not block the server from becoming ready.
    import asyncio
    startup_workers = [
        layers_worker.refresh_proxy_layers,
        github.fetch_all,
        rss.fetch_all,
        plugins.fetch_plugins,
        hub.fetch_hub,
        analytics.fetch_analytics,
        metabase.fetch_stats,
        scraper.scrape_all,
    ]
    for fn in startup_workers:
        asyncio.create_task(fn())

    log.info("Scheduler started with %d jobs, all workers fired on startup", len(_scheduler.get_jobs()))


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
