# justfile — task runner for QGIS OSINT Matrix (https://just.systems)
# Run `just` to list all available recipes.
# Inside `nix develop`, all tools are on PATH automatically.

# ── Default: list recipes ──────────────────────────────────────────────────────
default:
    @just --list

# ── Full native dev stack (no Docker) ───────────────────────────────────────
# Starts Postgres+PostGIS, Redis, FastAPI, and Vite in a single TUI with
# live logs and health-checked startup ordering.
# Requires `nix develop` (provides postgres, redis-server, process-compose).
# NOTE: closing the TUI does NOT stop the processes — run `just dev-stop` to
#       fully shut everything down.
dev:
    process-compose up --disable-dotenv

# Stop all native dev processes (postgres, redis, backend, frontend)
dev-stop:
    #!/usr/bin/env bash
    set -e
    PGDATA="$PWD/.dev-data/postgres"
    # Try the process-compose server first; fall back to direct process kills
    if process-compose down 2>/dev/null; then
        echo "process-compose: all processes stopped"
    else
        echo "process-compose server not running — killing processes directly"
        pg_ctl stop -D "$PGDATA" -m fast 2>/dev/null && echo "postgres stopped" || true
        redis-cli -p 6380 shutdown nosave 2>/dev/null && echo "redis stopped" || true
        ss -Htlnp 'sport = :8000' | grep -oP 'pid=\K[0-9]+' | xargs -r kill -9 2>/dev/null && echo "backend stopped" || true
        ss -Htlnp 'sport = :5173' | grep -oP 'pid=\K[0-9]+' | xargs -r kill -9 2>/dev/null && echo "frontend stopped" || true
    fi

# Run headless (no TUI) — raw logs streamed to stdout; useful for CI or tmux
dev-logs:
    process-compose up --disable-dotenv -t=false --no-server

# ── Backing services via Docker (alternative to native) ───────────────────
up:
    docker compose -f docker-compose.yml -f docker-compose.override.yml up -d db cache

down:
    docker compose down

# ── Database ───────────────────────────────────────────────────────────────────
migrate:
    cd backend && alembic upgrade head

migrate-down step="1":
    cd backend && alembic downgrade -{{ step }}

# ── Backend (FastAPI + hot-reload) ─────────────────────────────────────────────
backend: migrate
    cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ── Frontend (Vite dev server) ─────────────────────────────────────────────────
frontend:
    cd frontend && npm install && npm run dev


# ── Full Docker Compose stack ──────────────────────────────────────────────────
stack-up:
    docker compose -f docker-compose.yml -f docker-compose.override.yml up

stack-down:
    docker compose down

# ── Linting / type-checking ────────────────────────────────────────────────────
check-frontend:
    cd frontend && npm run check

# ── Seed / CLI shortcuts ───────────────────────────────────────────────────────
seed *args:
    cd backend && python -m app.cli {{ args }}
