"""RSS/Atom feed worker — news, blog, planet, mailing lists."""
from __future__ import annotations
import datetime
import logging
import feedparser
import httpx
from app.core.redis import cache_set_json, publish_sse

log = logging.getLogger(__name__)

# RSS/Atom feeds (feedparser)
RSS_FEEDS = [
    ("blog",   "https://blog.qgis.org/feed/",                     "#5bc8af", "BLOG"),
    ("planet", "https://planet.qgis.org/posts/index.xml",         "#818cf8", "PLANET"),
]

NEWS_JSON_URL = "https://feed.qgis.org/?json=1"

CACHE_TTLS = {
    "news":         2700,   # 3× the 900s fetch interval
    "blog":         5400,
    "planet":       2700,
    "changelog":    21600,
    "mailing_dev":  10800,
    "mailing_user": 10800,
}


def _parse_rss(url: str, channel: str, color: str, tag: str, limit: int = 50) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            # Prefer *_parsed (time.struct_time) → ISO 8601 so string sort works correctly.
            # Fall back to the raw string only when parsed form is unavailable.
            ts = ""
            parsed = (
                getattr(entry, "published_parsed", None)
                or getattr(entry, "updated_parsed", None)
            )
            if parsed:
                try:
                    ts = datetime.datetime(*parsed[:6], tzinfo=datetime.timezone.utc).isoformat()
                except Exception:
                    pass
            if not ts:
                ts = getattr(entry, "published", None) or getattr(entry, "updated", None) or ""

            author = ""
            if hasattr(entry, "author"):
                author = entry.author
            elif hasattr(feed.feed, "title"):
                author = feed.feed.title

            title = entry.get("title", "")[:150]
            link = entry.get("link", "")

            items.append({
                "id": f"{channel}:{link[-60:] if link else title[:30]}",
                "channel": channel,
                "title": title,
                "meta": f"{author} · {ts[:10] if ts else ''}",
                "author": author,
                "tag": tag,
                "tag_color": color,
                "color": color,
                "url": link,
                "published": ts,
                "timestamp": ts,
            })
        return items
    except Exception as exc:
        log.warning("RSS parse failed for %s: %s", url, exc)
        return []


async def _fetch_news_json() -> list[dict]:
    """Fetch news from feed.qgis.org JSON endpoint."""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(NEWS_JSON_URL)
            resp.raise_for_status()
            data = resp.json()
        items = []
        for entry in (data if isinstance(data, list) else []):
            ts_raw = entry.get("publish_from", 0)
            try:
                ts = datetime.datetime.fromtimestamp(float(ts_raw), tz=datetime.timezone.utc).isoformat()
            except Exception:
                ts = ""
            title = (entry.get("title") or "")[:150]
            url = entry.get("url") or ""
            items.append({
                "id": f"news:{entry.get('pk', title[:20])}",
                "channel": "news",
                "title": title,
                "meta": f"feed.qgis.org · {ts[:10] if ts else ''}",
                "author": "QGIS News",
                "tag": "NEWS",
                "tag_color": "#facc15",
                "color": "#facc15",
                "url": url,
                "published": ts,
                "timestamp": ts,
                "image": entry.get("image") or "",
                "content": (entry.get("content") or "")[:500],
            })
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        log.info("News JSON: got %d items", len(items))
        return items
    except Exception as exc:
        log.warning("News JSON fetch failed: %s", exc)
        return []


async def _fetch_changelog() -> list[dict]:
    url = "https://changelog.qgis.org/en/version/list/"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return []
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        for li in soup.select("ul li a")[:20]:
            text = li.get_text(strip=True)
            href = li.get("href", "")
            if text and href:
                items.append({
                    "id": f"changelog:{href}",
                    "channel": "changelog",
                    "title": text,
                    "meta": "changelog.qgis.org",
                    "tag": "REL",
                    "color": "#e05c5c",
                    "url": f"https://changelog.qgis.org{href}" if href.startswith("/") else href,
                    "timestamp": "",
                })
        return items
    except Exception as exc:
        log.warning("Changelog fetch failed: %s", exc)
        return []


async def fetch_all():
    log.info("RSS worker running...")

    # Parse RSS/Atom feeds
    for channel, url, color, tag in RSS_FEEDS:
        items = _parse_rss(url, channel, color, tag, limit=50)
        if items:
            items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            ttl = CACHE_TTLS.get(channel, 900)
            await cache_set_json(f"feed:{channel}", items, ttl=ttl)
            await publish_sse("feed_item", items[0])

    # Fetch QGIS news via JSON
    news_items = await _fetch_news_json()
    if news_items:
        await cache_set_json("feed:news", news_items, ttl=CACHE_TTLS["news"])
        await publish_sse("feed_item", news_items[0])

    changelog_items = await _fetch_changelog()
    if changelog_items:
        await cache_set_json("feed:changelog", changelog_items, ttl=CACHE_TTLS["changelog"])

    log.info("RSS worker done")
