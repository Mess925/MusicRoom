# Music Room — Backend

FastAPI backend for the Music Room platform. PostgreSQL for persistence, Redis
for caching/real-time state, [uv](https://docs.astral.sh/uv/) for dependencies,
Docker Compose for the dev environment.

> **Status: scaffolding.** The runtime is wired end to end and the API reference
> is live, but there is **no domain logic, no ORM models and no migrations yet**.
> The only endpoints are a service banner and a health check. See
> [What's included](#whats-included) for the exact inventory and
> [Not built yet](#not-built-yet) for what's deliberately missing.

---

## Prerequisites

| Tool           | Version              | Notes                                        |
| -------------- | -------------------- | -------------------------------------------- |
| Docker Engine  | 24+ with Compose v2  | The only hard requirement                     |
| `uv`           | 0.9+                 | Optional — only to change deps or run on host |

You do **not** need Python installed locally. Everything runs in containers.

---

## Running in dev

### 1. Create your `.env`

```sh
cp .env.example .env
```

`.env` is git-ignored and holds all configuration. Defaults work as-is; edit the
port variables if `8000`, `5432` or `6379` are already taken on your machine
(see [Port conflicts](#port-conflicts)).

### 2. Start the stack

```sh
docker compose up --build
```

First run pulls the Postgres/Redis images and builds the API image (~1–2 min).
Compose waits for the Postgres and Redis healthchecks to pass before starting
the API, so there is no start-order race.

Add `-d` to run detached: `docker compose up --build -d`.

### 3. Check it came up

```sh
curl localhost:8000/health
```

```json
{
  "status": "ok",
  "service": "Music Room API",
  "version": "0.1.0",
  "environment": "development",
  "database": "ok",
  "redis": "ok"
}
```

`"database"` and `"redis"` both reading `ok` means the API reached both
containers. Then open the interactive docs:

| URL                                  | What it is                            |
| ------------------------------------ | ------------------------------------- |
| http://localhost:8000/docs           | Swagger UI — try endpoints in-browser  |
| http://localhost:8000/redoc          | ReDoc — read-only reference            |
| http://localhost:8000/openapi.json   | Raw OpenAPI 3.1 schema                 |

### 4. Write code

`./src` is bind-mounted into the API container and Uvicorn runs with `--reload`.
**Save a file and the server restarts automatically — no rebuild, no restart.**
Watch it happen with `docker compose logs -f api`.

You only need to rebuild when dependencies change (see
[Adding a dependency](#adding-a-dependency)).

### 5. Stop

```sh
docker compose down       # stop; Postgres and Redis data survive
docker compose down -v    # stop and wipe the data volumes
```

---

## Everyday commands

```sh
docker compose up -d                # start in the background
docker compose logs -f api          # tail API logs (reload messages, tracebacks)
docker compose ps                   # what's running and healthy
docker compose restart api          # force-restart the API
docker compose build api            # rebuild after a dependency change
docker compose down                 # stop everything

# Shell into a service
docker compose exec api bash
docker compose exec postgres psql -U musicroom -d musicroom
docker compose exec redis redis-cli
```

### Port conflicts

Every published port is a variable, so nothing needs editing in
`docker-compose.yaml`. If Compose fails with `port is already allocated`, change
the value in `.env` and re-run `docker compose up -d`:

```sh
API_PORT=8001
POSTGRES_PORT=5433
REDIS_PORT=6380
```

These only affect access **from your host**. Container-to-container traffic uses
the internal service names (`postgres:5432`, `redis:6379`) and is unaffected.

### Adding a dependency

```sh
uv add <package>              # updates pyproject.toml + uv.lock
docker compose build api      # reinstall inside the image
docker compose up -d
```

No local `uv`? Run it through a container instead:

```sh
docker run --rm -v "$PWD":/w -w /w ghcr.io/astral-sh/uv:0.9.9-python3.13-bookworm-slim uv add <package>
```

The image installs with `uv sync --frozen`, so **`uv.lock` must be committed and
in sync with `pyproject.toml`** or the build fails.

### Running without Docker (optional)

You still need Postgres and Redis somewhere — easiest is to run just those:

```sh
docker compose up -d postgres redis
uv sync
# point .env at localhost (this is what .env.example ships)
uv run uvicorn app.main:app --reload --app-dir src
```

---

## What's included

### Services

| Service    | Image / build            | Host port | Purpose                              |
| ---------- | ------------------------ | --------- | ------------------------------------ |
| `api`      | local build, `development` target | `8000` | FastAPI + Uvicorn with `--reload` |
| `postgres` | `postgres:17-alpine`     | `5432`    | Primary datastore, volume `postgres_data` |
| `redis`    | `redis:8-alpine`         | `6379`    | Cache / real-time state, volume `redis_data`, AOF persistence on |

Postgres and Redis both declare healthchecks; `api` has
`depends_on: condition: service_healthy` on both.

### Endpoints

| Method | Path             | Description                                              |
| ------ | ---------------- | -------------------------------------------------------- |
| `GET`  | `/`              | Service banner: name, version, environment, doc links    |
| `GET`  | `/health`        | Pings Postgres (`SELECT 1`) and Redis (`PING`)           |
| `GET`  | `/docs`          | Swagger UI                                               |
| `GET`  | `/redoc`         | ReDoc                                                    |
| `GET`  | `/openapi.json`  | OpenAPI 3.1 schema                                       |

`/health` returns **200** when both dependencies answer and **503** when either
does not, with the failing one marked `"error"`:

```json
{ "status": "error", "database": "ok", "redis": "error", ... }
```

It opens no transactions and writes nothing, so it is safe to poll from an
orchestrator or uptime monitor.

### Key dependencies

| Package             | Version   | Role                                    |
| ------------------- | --------- | --------------------------------------- |
| `fastapi`           | 0.141.1   | Web framework, OpenAPI generation       |
| `uvicorn[standard]` | 0.52.4    | ASGI server                             |
| `sqlalchemy[asyncio]` | 2.0.52  | ORM — async engine and sessions         |
| `asyncpg`           | 0.31.0    | Async PostgreSQL driver                 |
| `alembic`           | 1.19.1    | Migrations — installed, not initialized |
| `redis`             | 8.1.0     | Async Redis client                      |
| `pydantic`          | 2.13.4    | Schemas and validation                  |
| `pydantic-settings` | 2.15.0    | Env-driven configuration                |
| `ruff`              | 0.16.3    | Lint + format (dev group)               |

Python 3.13 on `python:3.13-slim`. Exact pins live in `uv.lock`.

### Project layout

```
.
├── docker-compose.yaml     # api + postgres + redis, healthchecks, volumes
├── Dockerfile              # multi-stage: base → development / production
├── pyproject.toml          # dependencies (uv)
├── uv.lock                 # resolved versions — committed, used with --frozen
├── .env.example            # every configurable value, with defaults
├── REQUIREMENT.md          # the project spec this backend implements
└── src/app/
    ├── main.py             # FastAPI app, OpenAPI wiring, lifespan cleanup
    ├── api/
    │   ├── router.py       # aggregate router — mount new routers here
    │   └── routes/
    │       └── health.py   # GET /health
    ├── core/
    │   ├── config.py       # Settings, loaded from env / .env
    │   ├── openapi.py      # API description, tags, servers, Swagger UI options
    │   └── redis.py        # connection pool + get_redis dependency
    └── db/
        ├── base.py         # DeclarativeBase — ORM models subclass this
        └── session.py      # async engine + get_session dependency
```

### How to use the wiring

Both a database session and a Redis client are available as FastAPI
dependencies — no manual connection handling in routes:

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_session

router = APIRouter(tags=["rooms"])

@router.get("/rooms")
async def list_rooms(
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
): ...
```

New ORM models subclass `app.db.base.Base`. New routers get included in
`app/api/router.py`. New tags get a description in `app/core/openapi.py` so they
render as a described group in Swagger UI.

### Configuration

All settings come from the environment via `app.core.config.Settings`, with
`.env` as the local source. `.env` is git-ignored — **never commit secrets**.
`.env.example` is the documented template; keep it updated when you add a
variable.

| Variable                                       | Default              | Notes                                    |
| ---------------------------------------------- | -------------------- | ---------------------------------------- |
| `APP_NAME`, `ENVIRONMENT`, `DEBUG`             | Music Room API, development, true | Banner and error verbosity  |
| `API_PORT`, `POSTGRES_PORT`, `REDIS_PORT`      | 8000, 5432, 6379     | Host-side ports only                     |
| `POSTGRES_USER` / `_PASSWORD` / `_DB`          | musicroom ×3         | Also seed the Postgres container         |
| `DATABASE_URL`, `REDIS_URL`                    | localhost URLs       | Compose overrides these for the `api` service to use the internal hostnames |
| `DB_ECHO`                                      | false                | Log every SQL statement                  |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`              | 5, 10                | SQLAlchemy connection pool sizing        |
| `DOCS_ENABLED`, `DOCS_URL`, `REDOC_URL`, `OPENAPI_URL` | true, `/docs`, `/redoc`, `/openapi.json` | `DOCS_ENABLED=false` makes all three 404 |

### Production image

The Dockerfile is multi-stage; Compose uses `target: development`. Building
`--target production` instead gives you no dev dependencies, no `--reload`, and
a non-root `app` user:

```sh
docker build --target production -t musicroom-api:prod .
```

---

## Not built yet

Deliberately absent — this is the scaffold, not the application:

- **ORM models.** `db/base.py` holds an empty `Base`; no tables are defined and
  nothing creates a schema.
- **Migrations.** Alembic is installed but not initialized (no `alembic.ini`, no
  `versions/`). Run `alembic init` when the first model lands.
- **Auth.** No users, sessions, JWT, or social login.
- **Domain endpoints.** None of the services in `REQUIREMENT.md` (track vote,
  control delegation, playlist editor) exist.
- **Tests.** No test suite or CI.
- **Real-time transport.** No WebSocket layer yet.

## Troubleshooting

| Symptom                                       | Fix                                                                 |
| --------------------------------------------- | ------------------------------------------------------------------- |
| `port is already allocated`                   | Change the port in `.env`, `docker compose up -d`                    |
| `/health` returns 503 with `"database":"error"` | `docker compose ps` — is Postgres healthy? `docker compose logs postgres` |
| Code edits do nothing                         | Confirm the `./src:/app/src` mount and check `docker compose logs -f api` for reload lines |
| Build fails on `uv sync --frozen`             | `uv.lock` is stale — re-run `uv lock` and rebuild                    |
| `/docs` loads blank                           | Swagger UI/ReDoc fetch their JS/CSS from the jsDelivr CDN; the browser needs outbound internet |
