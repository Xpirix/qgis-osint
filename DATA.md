## Data loading & update mechanisms

### Architecture overview

```
External APIs / Files             data/locations/*.json
      │                                   │
      ▼                                   ▼
APScheduler workers (backend) ────── coordinate resolver
      │
      ├─► PostgreSQL/PostGIS  ──► REST /api/v1/layers/{name}  ──► MapLibre (static layers)
      │
      └─► Redis
            ├── layer:{name}    ──► REST /api/v1/layers/{name}  ──► MapLibre (dynamic layers)
            ├── feed:{channel}  ──► REST /api/v1/feeds/{name}   ──► Right panels (initial load)
            ├── stats:latest    ──► REST /api/v1/stats           ──► Left panel (initial load)
            └── SSE pub/sub     ──► GET /api/v1/stream           ──► Live push to all browsers
```

---

### Workers and their refresh intervals

| Worker | What it fetches | Interval | Also fires on |
|---|---|---|---|
| `github.py` | Commits (3 repos), releases, QEPs, repo stats | **5 min** | Startup |
| `rss.py` | QGIS News, Blog, Planet QGIS | **15 min** | Startup |
| `plugins.py` | Latest 50 plugins from `plugins.qgis.org/plugins/latest/` | **10 min** | Startup |
| `hub.py` | QGIS Hub resources (styles, models, etc.) | **30 min** | Startup |
| `metabase.py` | Plugin count/downloads, QGIS opens, hub typed counts | **60 min** | Startup |
| `layers.py` | Contributors GeoJSON + supporting GeoJSON (proxy cache) | **60 min** | Startup |
| `analytics.py` | QGIS version info (`version.qgis.org`) + Matomo country data | **24h** | Startup |
| `scraper.py` | Sustaining members (map pins), user groups, events | **24h** | Startup |

All workers fire **immediately on backend startup**, then on their interval.

---

### How "real-time" works

When a worker runs, it writes results into **two places**:
1. **Redis key** (`feed:{channel}`, `stats:latest`) — for REST polling on page load
2. **Redis pub/sub** (`SSE_CHANNEL`) — instantly relayed to every connected browser via `GET /api/v1/stream`

The browser opens one persistent SSE connection and receives `feed_item`, `stats_update`, and `layer_update` events without polling. So from a browser perspective, new commits or plugin updates appear **within 5–30 minutes of occurrence**, pushed automatically.

---

### Dynamic layers (auto-harvested, no CLI required)

Three layers are harvested live by `scraper.py` and stored as GeoJSON FeatureCollections in Redis. No manual seeding or PostgreSQL writes are involved.

| Layer | Source URL | Redis key | Coordinate file |
|---|---|---|---|
| `user_groups` | `https://raw.githubusercontent.com/qgis/QGIS/master/resources/data/user_groups_data.json` | `layer:user_groups` | None — joined with `data/countries_polygon.geojson` |
| `members` | `https://members.qgis.org/en/members/json/` | `layer:members` | None — right-panel list only, no map geometry |
| `events` | `https://raw.githubusercontent.com/qgis/QGIS/master/resources/data/qgis-hackfests.json` | `layer:events` | None — coordinates embedded in source GeoJSON |

The scraper runs **daily** (interval `fetch_interval_scrape = 86400`). On first startup it runs immediately, so map pins appear without any manual step.

---

### Static layers (seeded from YAML, stored in PostgreSQL)

These layers are **not auto-refreshed**. A human must edit the YAML files and re-run the seed command:

```bash
docker compose exec backend python -m app.cli seed
```

| Layer | File | Notes |
|---|---|---|
| Certified trainers | `data/seed/certified_trainers.yaml` | *(scaffold ready, data pending)* |
| Organisations | `data/seed/organisations.yaml` | *(scaffold ready, data pending)* |
| Mirrors | `data/seed/mirrors.yaml` | *(scaffold ready, data pending)* |

> **Legacy files:** `data/seed/user_groups.yaml`, `data/seed/sustaining_members.yaml`, and `data/seed/events.yaml` are no longer used by the live map. They are kept as historical reference only.

---

### Contributor/supporting member map layers (special case)

`contributors_map.json` and `supporting_map.json` are **not in PostgreSQL** — they are fetched from `qgis.org` and cached in Redis (`proxy:{filename}`, TTL 1h). The `layers.py` worker refreshes this cache every 60 minutes, with a fallback to `raw.githubusercontent.com`. These are auto-updated because qgis.org regenerates them via GitHub Actions.

---

### Summary by data type

| Data | Auto-updated? | Frequency | Mechanism |
|---|---|---|---|
| GitHub commits, releases, QEPs | ✅ Yes | 5 min | GitHub REST API → Redis → SSE |
| QGIS News / Blog / Planet | ✅ Yes | 15 min | RSS/Atom → Redis → SSE |
| Plugin repository | ✅ Yes | 10 min | HTML scrape → Redis → SSE |
| QGIS Hub resources | ✅ Yes | 30 min | Hub REST API → Redis → SSE |
| Metabase stats (counts, downloads, opens) | ✅ Yes | 60 min | Metabase public API → Redis → SSE |
| Contributor map pins | ✅ Yes | 60 min | qgis.org GeoJSON proxy → Redis |
| QGIS version info | ✅ Yes | 24h | version.qgis.org → Redis → SSE |
| Matomo country downloads | ✅ Yes | 24h | Matomo anonymous API → Redis |
| Sustaining members (stats count) | ✅ Yes | 24h | members.qgis.org JSON API → Redis |
| **User groups (map layer)** | ✅ Yes | 24h | GitHub JSON + country polygon join → Redis GeoJSON → map |
| **Sustaining members (map pins)** | ✅ Yes | 24h | Live scrape → Redis GeoJSON → map |
| **Events (map pins)** | ✅ Yes | 24h | GitHub GeoJSON (hackfests.json) → Redis GeoJSON → map |
| Certified trainers / Organisations / Mirrors | ❌ Manual | On demand | Edit YAML → `cli seed` → PostgreSQL |