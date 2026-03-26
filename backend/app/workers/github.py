"""GitHub feed worker — commits, releases, issues, QEPs."""
from __future__ import annotations
import asyncio
import datetime
import logging
import httpx
from app.core.config import settings
from app.core.redis import cache_get_json, cache_set_json, publish_sse

log = logging.getLogger(__name__)

# Repos fetched for commit feed — order is priority order for display
COMMIT_REPOS = [
    "qgis/QGIS",
    "qgis/QGIS-Documentation",
    "qgis/QGIS-Website",
]

# Bot accounts to filter from commit feeds
BOT_LOGINS = {
    "github-actions[bot]", "github-actions",
    "dependabot[bot]", "dependabot",
    "pre-commit-ci[bot]", "pre-commit-ci",
    "transifex-integration[bot]",
    "mergify[bot]", "mergify",
    "renovate[bot]", "renovate",
    # Note: "web-flow" (GitHub's PR merge committer) is intentionally NOT here —
    # it would filter out every pull-request merge commit.
}

# Substrings in the raw git author/committer email that indicate automation
BOT_EMAIL_MARKERS = (
    "[bot]",
    "noreply.github.com",
    "transifex",
    "github-actions",
)

# Commit message prefixes/substrings produced by automated tooling
BOT_MSG_PATTERNS = (
    "update translations",
    "bump version",
    "chore(deps)",
    "chore(release)",
    "auto-update",
    "automated commit",
    "[skip ci]",
)

TAG_COLOURS = {
    "FIX": "#ee7913",
    "FEAT": "#93b023",
    "DOCS": "#5bc8af",
    "REF": "#a8c4e0",
    "QEP": "#f0e64a",
    "REL": "#e05c5c",
    "OTHER": "#c8d8e8",
}


def _interleave_prioritised(per_repo: dict[str, list[dict]], limit: int = 100) -> list[dict]:
    """Interleave commits across repos, giving qgis/QGIS double weight.

    Pattern per cycle: QGIS, QGIS, Docs, QGIS, QGIS, Website — so the main
    repo always dominates the visible feed without hiding the others entirely.
    """
    iterators = {repo: iter(items) for repo, items in per_repo.items()}
    # Cycle pattern: 3× QGIS, 1× Docs, 1× Website per round
    pattern = [
        "qgis/QGIS", "qgis/QGIS", "qgis/QGIS",
        "qgis/QGIS-Documentation",
        "qgis/QGIS-Website",
    ]
    result: list[dict] = []
    exhausted: set[str] = set()
    while len(result) < limit and len(exhausted) < len(iterators):
        for repo in pattern:
            if repo in exhausted:
                continue
            it = iterators.get(repo)
            if it is None:
                exhausted.add(repo)
                continue
            try:
                result.append(next(it))
            except StopIteration:
                exhausted.add(repo)
            if len(result) >= limit:
                break
    return result


def _classify_commit(message: str) -> tuple[str, str]:
    msg = message.lower()
    if any(k in msg for k in ("fix", "bug", "revert")):
        return "FIX", TAG_COLOURS["FIX"]
    if any(k in msg for k in ("feat", "add", "new", "implement")):
        return "FEAT", TAG_COLOURS["FEAT"]
    if any(k in msg for k in ("doc", "readme", "changelog")):
        return "DOCS", TAG_COLOURS["DOCS"]
    if any(k in msg for k in ("refactor", "clean", "lint", "format", "style")):
        return "REF", TAG_COLOURS["REF"]
    if "release" in msg:
        return "REL", TAG_COLOURS["REL"]
    return "OTHER", TAG_COLOURS["OTHER"]


async def _fetch_commits(client: httpx.AsyncClient, repo: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/commits?per_page=50"
    try:
        resp = await client.get(url, headers=settings.github_headers, timeout=15.0)
        resp.raise_for_status()
        commits = resp.json()
        items = []
        for c in commits:
            # Determine author and committer logins independently
            author_login = (c.get("author") or {}).get("login", "").lower()
            committer_login = (c.get("committer") or {}).get("login", "").lower()
            # Check raw git email (catches bots whose GitHub account is null)
            author_email = (
                c.get("commit", {}).get("author", {}).get("email", "")
                or c.get("commit", {}).get("committer", {}).get("email", "")
            ).lower()
            # Check commit message for automated-tooling patterns
            raw_msg = c.get("commit", {}).get("message", "").split("\n")[0].lower()

            # Author: full BOT_LOGINS check (includes web-flow for web-editor commits)
            # Committer: only [bot] suffix — "web-flow" is GitHub's legitimate PR merge
            #            committer and must NOT be filtered here or all PR merges vanish.
            if (
                author_login in BOT_LOGINS
                or "[bot]" in author_login
                or "[bot]" in committer_login
                or any(m in author_email for m in BOT_EMAIL_MARKERS)
                or any(p in raw_msg for p in BOT_MSG_PATTERNS)
            ):
                continue
            msg = c.get("commit", {}).get("message", "").split("\n")[0][:120]
            author = (
                c.get("commit", {}).get("author", {}).get("name", "")
                or author_login
                or "unknown"
            )
            # Use committer date (when commit landed in the repo) not author date
            # (when the patch was written). Author date can be days old for PRs
            # that sit in review, causing commits to sort far below recent entries.
            ts = (
                c.get("commit", {}).get("committer", {}).get("date", "")
                or c.get("commit", {}).get("author", {}).get("date", "")
            )
            sha = c.get("sha", "")[:8]
            tag, color = _classify_commit(msg)
            avatar_url = (c.get("author") or {}).get("avatar_url", "")
            items.append({
                "id": f"{repo}:{sha}",
                "channel": "commits",
                "repo": repo,
                "title": msg,
                "meta": f"{author} · {ts[:10] if ts else ''}",
                "author": author,
                "avatar_url": avatar_url,
                "tag": tag,
                "color": color,
                "url": c.get("html_url", ""),
                "published": ts,
                "timestamp": ts,
            })
        return items
    except Exception as exc:
        log.warning("GitHub commits fetch failed for %s: %s", repo, exc)
        return []


async def _fetch_qeps(client: httpx.AsyncClient) -> list[dict]:
    url = "https://api.github.com/repos/qgis/QGIS-Enhancement-Proposals/issues?state=open&per_page=20"
    try:
        resp = await client.get(url, headers=settings.github_headers, timeout=15.0)
        resp.raise_for_status()
        issues = resp.json()
        items = []
        for issue in issues:
            items.append({
                "id": f"qep:{issue['number']}",
                "channel": "qeps",
                "repo": "qgis/QGIS-Enhancement-Proposals",
                "title": issue.get("title", "")[:120],
                "meta": f"#{issue['number']} · {issue.get('user', {}).get('login', '')}",
                "tag": "QEP",
                "color": TAG_COLOURS["QEP"],
                "url": issue.get("html_url", ""),
                "timestamp": issue.get("created_at", ""),
            })
        return items
    except Exception as exc:
        log.warning("GitHub QEPs fetch failed: %s", exc)
        return []


async def _fetch_repo_stats(client: httpx.AsyncClient) -> dict:
    url = "https://api.github.com/repos/qgis/QGIS"
    try:
        resp = await client.get(url, headers=settings.github_headers, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        return {
            "github_stars": data.get("stargazers_count", 0),
            "github_forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
        }
    except Exception as exc:
        log.warning("GitHub repo stats fetch failed: %s", exc)
        return {}


async def fetch_all():
    log.info("GitHub worker running...")
    async with httpx.AsyncClient() as client:
        # Fetch all repos and QEPs + repo stats in parallel
        results = await asyncio.gather(
            *[_fetch_commits(client, repo) for repo in COMMIT_REPOS],
            _fetch_qeps(client),
            _fetch_repo_stats(client),
            return_exceptions=True,
        )

        per_repo: dict[str, list[dict]] = {}
        for repo, result in zip(COMMIT_REPOS, results[:len(COMMIT_REPOS)]):
            if isinstance(result, list):
                per_repo[repo] = result
            else:
                log.warning("Commits fetch error for %s: %s", repo, result)
                per_repo[repo] = []

        qep_result = results[len(COMMIT_REPOS)]
        qep_items: list[dict] = qep_result if isinstance(qep_result, list) else []

        stats_result = results[len(COMMIT_REPOS) + 1]
        repo_stats: dict = stats_result if isinstance(stats_result, dict) else {}

        all_commits = _interleave_prioritised(per_repo, limit=100)

        # Store in Redis — TTL is 3× the fetch interval to survive scheduler jitter
        await cache_set_json("feed:commits", all_commits, ttl=900)
        await cache_set_json("feed:qeps", qep_items[:50], ttl=1800)

        # Publish top 15 commits as SSE — _interleave_prioritised already ensures
        # qgis/QGIS appears as 3 out of every 5 slots.
        for item in all_commits[:15]:
            await publish_sse("feed_item", item)

        # Update stats
        if repo_stats:
            stats = await cache_get_json("stats:latest") or {}
            stats.update(repo_stats)
            stats["open_qeps"] = len(qep_items)
            stats["generated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            await cache_set_json("stats:latest", stats, ttl=600)
            await publish_sse("stats_update", stats)

    total = sum(len(v) for v in per_repo.values())
    log.info("GitHub worker done: %d commits (%s), %d qeps",
             total, ", ".join(f"{r.split('/')[1]}={len(v)}" for r, v in per_repo.items()),
             len(qep_items))
