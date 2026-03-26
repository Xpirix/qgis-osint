"""FastAPI application factory with lifespan management."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.redis import get_redis, close_redis
from app.api.v1 import proxy, layers, feeds, stats, stream
from app.workers.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=settings.log_level)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting QGIS OSINT Matrix backend...")
    await get_redis()
    await start_scheduler()
    yield
    log.info("Shutting down...")
    await stop_scheduler()
    await close_redis()


app = FastAPI(
    title="QGIS OSINT Matrix API",
    description="Real-time geospatial intelligence dashboard for the QGIS ecosystem.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Routers
app.include_router(proxy.router, prefix="/api/v1/proxy", tags=["proxy"])
app.include_router(layers.router, prefix="/api/v1/layers", tags=["layers"])
app.include_router(feeds.router, prefix="/api/v1/feeds", tags=["feeds"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(stream.router, prefix="/api/v1/stream", tags=["stream"])


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
