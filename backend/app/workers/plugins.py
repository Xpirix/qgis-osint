"""plugins.qgis.org feed worker.

Fetches the 50 most-recently-updated plugins from the plugins.qgis.org website.
The /plugins/latest/ page is sorted by latest_version_date and lists plugins
across all QGIS versions — it is the canonical "what just got updated" view.

There is no JSON/REST API; the page returns HTML which we parse with the
standard library HTMLParser (no extra dependencies required).

Plugin counts and download totals come from the Metabase worker.
"""
from __future__ import annotations
import logging
from html.parser import HTMLParser
import httpx
from app.core.redis import cache_get_json, cache_set_json, publish_sse

log = logging.getLogger(__name__)

PLUGINS_LATEST_URL = (
    "https://plugins.qgis.org/plugins/latest/"
    "?sort=latest_version_date&order=desc&per_page=50"
)


class _PluginTableParser(HTMLParser):
    """Extracts plugin rows from the plugins.qgis.org latest-plugins table.

    Each row has the structure (columns in order):
      icon | name (link) | downloads | author | updated | created | rating | stable_ver | exp_ver
    The row <tr> carries id="pmain{plugin_id}".
    """

    def __init__(self) -> None:
        super().__init__()
        self.plugins: list[dict] = []
        self._row: dict = {}
        self._in_row = False
        self._capture: str | None = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        a = dict(attrs)
        if tag == "tr" and a.get("id", "").startswith("pmain"):
            self._in_row = True
            self._row = {"id": a["id"][5:]}
            return
        if not self._in_row:
            return
        if tag == "a" and "plugin-name" in a.get("class", ""):
            # href="/plugins/{slug}/"
            slug = a.get("href", "").strip("/").split("/")[-1]
            self._row["slug"] = slug
            self._capture = "name"
        elif tag == "a" and a.get("class") == "author":
            self._capture = "author"
        elif tag == "span" and "user-timezone-short-naturalday" in a.get("class", ""):
            # The span text is a human-readable relative string ("18 minutes ago").
            # The ISO 8601 timestamp is in the title attribute — prefer that.
            title = a.get("title", "").strip()
            if title:
                self._row["updated"] = title
            else:
                self._capture = "updated"
        elif tag == "a" and "stable" in a.get("title", ""):
            self._capture = "version"

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._in_row and self._row.get("name"):
            self.plugins.append(self._row)
            self._in_row = False
            self._row = {}
        self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture and self._in_row:
            v = data.strip()
            if v:
                self._row[self._capture] = v
                self._capture = None


def _parse_plugins_html(html: str) -> list[dict]:
    parser = _PluginTableParser()
    parser.feed(html)
    items = []
    for pl in parser.plugins:
        slug      = pl.get("slug", pl.get("id", ""))
        name      = pl.get("name", slug)
        version   = pl.get("version", "")
        author    = pl.get("author", "").strip()
        update_ts = pl.get("updated", "")
        # update_ts is ISO 8601 with timezone, e.g. "2026-03-21T11:44:16.403006+00:00"
        update_date = update_ts[:10] if update_ts else ""
        items.append({
            "id":        f"plugin:{pl['id']}",
            "channel":   "plugins",
            "title":     f"{name} v{version}" if version else name,
            "meta":      f"{author} · {update_date}",
            "author":    author,
            "tag":       "PLUGIN",
            "color":     "#ee7913",
            "url":       f"https://plugins.qgis.org/plugins/{slug}/",
            "published": update_date,
            "timestamp": update_ts,   # ISO 8601 from title attr — used for dedup
        })
    return items


async def fetch_plugins() -> None:
    log.info("Plugins worker running...")
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(
                PLUGINS_LATEST_URL,
                headers={"User-Agent": "Mozilla/5.0 (QGIS-OSINT-Matrix)"},
            )
            resp.raise_for_status()

        items = _parse_plugins_html(resp.text)

        if items:
            # Compare with the previous cache to find plugins that are genuinely
            # new or have been updated (same ID, newer ISO timestamp) since the
            # last fetch.  Only those are pushed via SSE.
            prev_ts: dict[str, str] = {
                i["id"]: i.get("timestamp", "")
                for i in (await cache_get_json("feed:plugins") or [])
            }
            new_or_updated = [
                i for i in items
                if i["id"] not in prev_ts
                or i.get("timestamp", "") > prev_ts[i["id"]]
            ]

            # TTL is 3× the fetch interval so the cache survives any scheduler jitter
            await cache_set_json("feed:plugins", items, ttl=1800)

            for item in new_or_updated:
                await publish_sse("feed_item", item)

        log.info(
            "Plugins worker done: %d plugins parsed, %d new/updated",
            len(items),
            len(new_or_updated) if items else 0,
        )

    except Exception as exc:
        log.warning("Plugins worker failed: %s", exc)
