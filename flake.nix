{
  description = "QGIS OSINT Matrix — development environment";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = false;
        };

        # ── Python environment ───────────────────────────────────────────────
        python = pkgs.python313;

        # Postgres 16 with PostGIS extension bundled
        postgresWithPostGIS = pkgs.postgresql_16.withPackages (ps: [ ps.postgis ]);

        pythonEnv = python.withPackages (ps: with ps; [
          # Web framework
          fastapi
          uvicorn
          # Database
          sqlalchemy
          asyncpg
          geoalchemy2
          alembic
          psycopg2
          # HTTP / feeds
          httpx
          feedparser
          beautifulsoup4
          lxml
          # Scheduling / caching
          apscheduler
          redis
          # Config / validation
          pydantic
          pydantic-settings
          python-dotenv
          # CLI tooling
          typer
          rich
          # Misc
          geojson
          pyyaml
        ]);

      in {
        # ── Dev shell ────────────────────────────────────────────────────────
        devShells.default = pkgs.mkShell {
          name = "qgis-osint-matrix";

          packages = [
            pythonEnv

            # Node / frontend tooling
            pkgs.nodejs_22
            pkgs.nodePackages.npm

            # Native Postgres 16 + PostGIS + Redis (no Docker needed for dev)
            postgresWithPostGIS   # postgres, initdb, pg_isready, psql, createdb
            pkgs.redis            # redis-server + redis-cli

            # Full-stack process orchestrator (replaces docker-compose for dev)
            pkgs.process-compose

            # Docker (still available for the production stack)
            pkgs.docker
            pkgs.docker-compose

            # Useful dev utilities
            pkgs.just
            pkgs.httpie
            pkgs.jq
            pkgs.curl
            pkgs.git
            pkgs.psmisc        # fuser, killall, pstree
            pkgs.iproute2      # ss
          ];

          # ── Environment variables ──────────────────────────────────────────
          # Loaded from .env by pydantic-settings at runtime; these are only
          # shell-level defaults so the app can start without a .env file.
          shellHook = ''
            # ── Banner ──────────────────────────────────────────────────────
            echo ""
            echo "  🌍  QGIS OSINT Matrix — dev shell"
            echo "  Python  : $(python --version)"
            echo "  Node    : $(node --version)"
            echo "  npm     : $(npm --version)"
            echo ""
            echo "  Full-stack dev (no Docker):"
            echo "    just dev      — Postgres + Redis + backend + frontend (TUI)"
            echo "    just dev-stop — stop all background dev processes"
            echo ""
            echo "  Individual processes:"
            echo "    just up            — start Docker db + Redis only"
            echo "    just backend-dev   — FastAPI --reload on :8000"
            echo "    just frontend-dev  — Vite dev server on :5173"
            echo "    just migrate       — alembic upgrade head"
            echo ""

            # ── Default env if .env does not exist ──────────────────────────
            if [ ! -f .env ]; then
              echo "  ⚠  No .env found — using built-in defaults."
              echo "     Copy .env.example to .env and fill in secrets."
              echo ""
              export POSTGRES_HOST=localhost
              export POSTGRES_PORT=5433
              export POSTGRES_DB=osint_matrix
              export POSTGRES_USER=qgis
              export POSTGRES_PASSWORD=devpassword
              export REDIS_URL=redis://localhost:6380/0
              export LOG_LEVEL=DEBUG
            fi

            # ── Ensure local data directories exist ──────────────────────────
            mkdir -p .dev-data/postgres .dev-data/redis .dev-data/logs

            # ── Convenience aliases ──────────────────────────────────────────
            alias up='docker compose -f docker-compose.yml -f docker-compose.override.yml up -d db cache'
            alias down='docker compose down'
            alias backend-dev='(cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload)'
            alias frontend-dev='(cd frontend && npm install && npm run dev)'
            alias migrate='(cd backend && alembic upgrade head)'
          '';
        };
      }
    );
}
