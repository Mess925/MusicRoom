# Music Room

A mobile, connected, and collaborative music application — built as part of the 42 curriculum.

## Overview

Music Room lets people at a shared event collaboratively control music playback through two core services:

- **Music Track Vote** — Live event playlist where attendees suggest and vote for the next track.
- **Music Control Delegation** — Device owners can delegate playback control to specific friends, per device.

## Architecture

```
Swift/SwiftUI iOS App
        |
        | REST API (JSON) over HTTP
        v
FastAPI backend, run via Uvicorn
        |
        | SQL queries (psycopg2)
        v
PostgreSQL database
```

The mobile application acts strictly as a "remote control" — no business logic or persistent state lives on the client. The backend is the single source of truth for all data.

## Tech stack and justification

| Layer | Choice | Why |
|---|---|---|
| Mobile client | Swift + SwiftUI | Native iOS performance and tooling; team's existing expertise |
| Backend framework | FastAPI (Python) | Automatically generates interactive Swagger/OpenAPI documentation from route definitions, satisfying the project's API documentation requirement with minimal manual upkeep. Built-in request validation via type hints reduces boilerplate compared to manually parsing/validating requests. |
| Server | Uvicorn | ASGI server required to actually run a FastAPI application; supports async request handling needed for real-time features. |
| Database | PostgreSQL | Relational structure fits the project's clearly related entities (users, events, tracks, votes, devices). Provides atomic row-level updates (e.g. `votes = votes + 1`), which is the mechanism used to safely handle concurrent votes/edits without race conditions. |
| API style | REST (JSON) | Simple, well-understood convention for exposing resource-based operations (events, tracks, votes, devices) via standard HTTP methods. |
| Auth | JWT + bcrypt (planned) | Stateless authentication appropriate for a REST API — no server-side session storage required between requests. |

**Alternatives considered:** Node.js/Express was our initial choice and was fully implemented and tested (see git history) before switching to FastAPI. Node/Express offers stronger native real-time support via Socket.io, but we moved to FastAPI for its automatic OpenAPI documentation generation and built-in data validation, which reduced the risk of our API contract and documentation drifting out of sync during development.

## Project structure

```
MusicRoom/
├── MusicRoom/              SwiftUI iOS client
├── MusicRoomBackend/        FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   ├── .env                 not committed — see Setup
│   └── venv/                 not committed
├── .gitignore
└── README.md
```

## Setup

### Prerequisites
- Python 3.x
- PostgreSQL

### Backend

```bash
cd MusicRoomBackend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `MusicRoomBackend/` with:

```
DB_USER=<your_db_user>
DB_PASSWORD=<your_db_password>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=music_room
JWT_SECRET=<your_secret>
PORT=3000
```

Create the database:

```bash
psql postgres -c "CREATE DATABASE music_room;"
```

Run the server:

```bash
uvicorn main:app --reload --port 3000
```

API documentation is auto-generated and available at `http://localhost:3000/docs` while the server is running.

### iOS App

Open `MusicRoom/MusicRoom.xcodeproj` in Xcode. Configure the backend base URL to point to your running backend instance.

## Status

- [x] Backend scaffolding (FastAPI + PostgreSQL connection)
- [ ] Database schema
- [ ] Authentication
- [ ] Music Track Vote
- [ ] Music Control Delegation
- [ ] Real-time layer
- [ ] Security/logging
- [ ] Load testing
- [ ] Frontend UI