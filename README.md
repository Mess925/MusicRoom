# Music Room

A mobile, connected, and collaborative music application — built as part of the 42 curriculum.

Two components live in this repo: a native SwiftUI iOS client and a FastAPI
backend. The backend is the single source of truth; the client is a remote
control that holds no authoritative state and performs no business logic locally.

> **Status: scaffolding.** The backend runtime is wired end to end (FastAPI +
> Postgres + Redis under Docker Compose, live OpenAPI reference) but has no
> domain logic, ORM models or migrations yet. The iOS app is still the Xcode
> template. See [Status](#status).

## Core services

Defined in [`MusicRoomBackend/REQUIREMENT.md`](MusicRoomBackend/REQUIREMENT.md):

- **Music Track Vote** — live event playlist where attendees suggest and vote for the next track.
- **Music Control Delegation** — device owners delegate playback control to specific friends, per device.
- **Music Playlist Editor** — real-time, multi-user collaborative playlist editing with conflict-free concurrent edits.

## Architecture

```
Swift/SwiftUI iOS App
        |
        | REST API (JSON) over HTTP
        v
FastAPI backend, run via Uvicorn        ── Redis (cache / real-time state)
        |
        | async SQL (SQLAlchemy + asyncpg)
        v
PostgreSQL database
```

All three services run as containers under Docker Compose in development.

## Tech stack and justification

| Layer | Choice | Why |
|---|---|---|
| Mobile client | Swift + SwiftUI | Native iOS performance and tooling; team's existing expertise |
| Backend framework | FastAPI (Python 3.13) | Generates the interactive Swagger/OpenAPI reference straight from route definitions, satisfying the project's API documentation requirement with minimal manual upkeep. Type-hint request validation cuts boilerplate. |
| Server | Uvicorn | ASGI server required to run FastAPI; async request handling is needed for the real-time features. |
| Database | PostgreSQL 17 | Relational structure fits the clearly related entities (users, events, tracks, votes, devices). Atomic row-level updates are the mechanism for handling concurrent votes and playlist edits without race conditions. |
| DB access | SQLAlchemy 2 (async) + asyncpg | Async driver keeps database calls off the event loop; the ORM gives a single place to declare the schema, with Alembic for migrations. |
| Cache / real-time state | Redis 8 | Ephemeral shared state (vote tallies, presence, pub/sub fan-out) that should not hit Postgres on every read. |
| API style | REST (JSON) | Well-understood convention for resource-based operations (events, tracks, votes, devices) over standard HTTP methods. |
| Auth | JWT + social token verification (planned) | Stateless authentication appropriate for a REST API — no server-side session storage between requests. External SDKs only produce a token the backend verifies. |
| Dependencies | uv + `uv.lock` | Lockfile-driven, reproducible installs; no third-party libraries committed to the repo, per the subject. |
| Dev environment | Docker Compose | One command brings up API, Postgres and Redis with healthchecks — no local Python or database install needed. |

**Alternatives considered:** Node.js/Express was our initial choice and was
fully implemented and tested (see git history) before switching to FastAPI.
Node/Express offers stronger native real-time support via Socket.io, but we
moved to FastAPI for its automatic OpenAPI documentation generation and built-in
data validation, which reduced the risk of our API contract and documentation
drifting out of sync during development.

## Repository layout

```
MusicRoom/
├── MusicRoom/                  SwiftUI iOS client
│   ├── MusicRoom.xcodeproj
│   └── MusicRoom/              app sources
├── MusicRoomBackend/           FastAPI backend — see its README
│   ├── docker-compose.yaml     api + postgres + redis
│   ├── Dockerfile              multi-stage: development / production
│   ├── pyproject.toml          dependencies (uv)
│   ├── uv.lock                 resolved versions — committed
│   ├── .env.example            every configurable value, with defaults
│   ├── .env                    not committed
│   ├── REQUIREMENT.md          the project spec
│   ├── README.md
│   └── src/app/                application package
├── .gitignore
└── README.md
```

## Getting started

### Backend

Docker Engine 24+ with Compose v2 is the only hard requirement — no local Python
needed.

```bash
cd MusicRoomBackend
cp .env.example .env
docker compose up --build
curl localhost:8000/health
```

The interactive API reference is at `http://localhost:8000/docs`
(ReDoc at `/redoc`, raw schema at `/openapi.json`).

[`MusicRoomBackend/README.md`](MusicRoomBackend/README.md) is the authoritative
guide: everyday Compose commands, port conflicts, adding dependencies, running
without Docker, configuration reference, and troubleshooting.

### iOS App

Open `MusicRoom/MusicRoom.xcodeproj` in Xcode. Configure the backend base URL to
point to your running backend instance (`http://localhost:8000` by default).

## Status

- [x] Backend scaffolding — FastAPI, Postgres, Redis, Docker Compose, healthcheck, OpenAPI reference
- [ ] Database schema (ORM models)
- [ ] Migrations (Alembic installed, not initialized)
- [ ] Authentication
- [ ] Music Track Vote
- [ ] Music Control Delegation
- [ ] Music Playlist Editor
- [ ] Real-time layer (WebSocket)
- [ ] Security/logging
- [ ] Tests and CI
- [ ] Load testing
- [ ] Frontend UI
