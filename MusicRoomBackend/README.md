# Music Room — Backend

FastAPI backend for the Music Room platform. PostgreSQL for persistence, Redis
for caching/real-time state, [uv](https://docs.astral.sh/uv/) for dependencies,
Docker Compose for the dev environment.

> **Status: scaffolding.** The runtime is wired end to end and the API reference
> is live, but there is **no domain logic, no ORM models and no migrations yet**.
> The only endpoints are a service banner and a health check. See
> [What's included](#whats-included) for the exact inventory and
> [Not built yet](#not-built-yet) for what's deliberately missing. The test
> harness is wired up — see [Testing](#testing).

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

./test.sh                           # run the tests (see Testing)

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

## Testing

`pytest` + `pytest-asyncio`, driven by one script at the repo root:

```sh
./test.sh                    # unit tests
./test.sh --cov              # unit tests + coverage report
./test.sh --integration      # only the integration tests
./test.sh --all              # unit + integration
./test.sh -- -k health -vv   # anything after `--` is passed to pytest
./test.sh --help             # all options
```

The script picks its own runner: **host** if you have `uv` installed, otherwise
the **`api` container** — reusing the running one when the stack is up, or
starting a throwaway one when it is not. Force either with `--host` / `--docker`.

### Two kinds of test

| Kind            | Needs Postgres/Redis? | How                                                                       |
| --------------- | --------------------- | ------------------------------------------------------------------------- |
| **unit**        | No                    | `get_session` / `get_redis` are replaced with the fakes in `tests/fakes.py` via `app.dependency_overrides` |
| **integration** | Yes                   | Marked `@pytest.mark.integration`; talk to the real engine and Redis pool  |

Integration tests are **deselected by default** (`-m "not integration"`), so the
default run needs nothing running and finishes in well under a second.
`--integration` / `--all` bring up Postgres and Redis first (Compose waits for
their healthchecks).

### Writing a test

Request the `client` fixture — it is an `httpx.AsyncClient` bound to the real
app in-process, with healthy fake backends already installed. `asyncio_mode` is
`auto`, so `async def` tests need no marker:

```python
async def test_rooms_are_listed(client):
    response = await client.get("/rooms")

    assert response.status_code == 200
```

To exercise a failure path, swap in a failing fake before the request:

```python
from tests.fakes import FakeRedis

async def test_degrades_without_cache(client, override):
    override(redis=FakeRedis(fail=True))

    assert (await client.get("/health")).status_code == 503
```

Fixtures live in `tests/conftest.py`:

| Fixture      | What it gives you                                                        |
| ------------ | ------------------------------------------------------------------------ |
| `client`     | `AsyncClient` on the app, with healthy fake Postgres + Redis              |
| `raw_client` | `AsyncClient` on the app with **no** overrides — real services (integration) |
| `app`        | The `FastAPI` instance; overrides are cleared after each test             |
| `session`    | The healthy `FakeSession` behind `client` — inspect `.statements`          |
| `redis`      | The healthy `FakeRedis` behind `client` — inspect `.pings` / `.store`      |
| `override`   | `override(session=..., redis=...)` to install different fakes             |

`tests/conftest.py` pins `APP_NAME`, `API_VERSION`, `ENVIRONMENT`, `DEBUG` and
`DOCS_ENABLED` in the environment **before** importing `app`, because
`Settings` is built and cached at import time — so results do not depend on your
local `.env`. `DATABASE_URL` and `REDIS_URL` are left alone: unit tests never
connect, and integration tests should use the real ones.

The whole suite shares **one event loop**
(`asyncio_default_test_loop_scope = "session"`). The async engine and Redis
connection pool are module-level singletons that bind to the loop that first
uses them, so per-test loops would hand later tests connections from a closed
loop.

As the fakes only implement what the routes currently call, extend
`tests/fakes.py` as routes start committing, flushing or querying models — a
fake that lags behind the real client is worse than no fake at all.

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
| `pytest`            | 9.1.1     | Test runner (dev group)                 |
| `pytest-asyncio`    | 1.4.0     | `async def` tests, `asyncio_mode = auto` (dev group) |
| `pytest-cov`        | 7.1.0     | Coverage reporting (dev group)           |
| `httpx`             | 0.28.1    | In-process ASGI test client (dev group)  |

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
├── test.sh                 # test runner — host or container, unit or integration
├── tests/
│   ├── conftest.py         # env pinning, fake-backed client, override helper
│   ├── fakes.py            # FakeSession / FakeRedis stand-ins
│   ├── test_app.py         # wiring: routes mounted, OpenAPI schema, docs pages
│   ├── test_config.py      # Settings defaults, DSN parsing, caching
│   ├── test_health.py      # GET /health, healthy and degraded
│   ├── test_root.py        # GET /
│   └── integration/        # marked `integration` — real Postgres + Redis
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
- **CI.** No pipeline — the suite exists (`./test.sh`) but nothing runs it on
  push.
- **Real-time transport.** No WebSocket layer yet.

## Troubleshooting

| Symptom                                       | Fix                                                                 |
| --------------------------------------------- | ------------------------------------------------------------------- |
| `port is already allocated`                   | Change the port in `.env`, `docker compose up -d`                    |
| `/health` returns 503 with `"database":"error"` | `docker compose ps` — is Postgres healthy? `docker compose logs postgres` |
| Code edits do nothing                         | Confirm the `./src:/app/src` mount and check `docker compose logs -f api` for reload lines |
| Build fails on `uv sync --frozen`             | `uv.lock` is stale — re-run `uv lock` and rebuild                    |
| `/docs` loads blank                           | Swagger UI/ReDoc fetch their JS/CSS from the jsDelivr CDN; the browser needs outbound internet |
| `./test.sh` says `no module named pytest`     | The image predates the dev deps — `docker compose build api` |
| Integration tests fail with `database: error` | Postgres/Redis are not up: `docker compose up -d postgres redis` |
