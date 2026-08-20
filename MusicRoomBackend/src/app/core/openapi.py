"""OpenAPI / Swagger UI metadata for the API reference at `/docs`."""

DESCRIPTION = """
Backend API for **Music Room** — the single source of truth for the platform.
Mobile clients act as remote controls: they hold no authoritative state and
perform no business logic locally.

This deployment is **scaffolding only**. The service, database and cache
connections are wired up and observable through `GET /health`; no domain
endpoints exist yet.

### Conventions

* All payloads are JSON (`application/json`).
* Timestamps are ISO 8601 in UTC.
* Errors use the standard FastAPI shape: `{"detail": ...}`.
* The base URL is configurable per environment — pick one from the
  **Servers** dropdown above, or point your client at your own host.
"""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Liveness and dependency readiness probes. Used by "
        "Docker, orchestrators and uptime monitoring.",
    },
    {
        "name": "root",
        "description": "Service banner and pointers to the API reference.",
    },
]

CONTACT = {
    "name": "Music Room Backend",
    "url": "https://github.com/thanthtetaung/MusicRoom",
}

LICENSE_INFO = {
    "name": "MIT",
    "identifier": "MIT",
}

SERVERS = [
    {"url": "http://localhost:8000", "description": "Local development"},
]

# Swagger UI front-end options: https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
SWAGGER_UI_PARAMETERS = {
    "docExpansion": "list",          # expand tag groups, collapse operations
    "defaultModelsExpandDepth": 1,   # show the schema list, collapsed
    "displayRequestDuration": True,  # show ms taken by "Try it out" calls
    "filter": True,                  # search box over operations
    "persistAuthorization": True,    # keep credentials across reloads
    "tryItOutEnabled": True,         # "Try it out" active by default
    "syntaxHighlight.theme": "obsidian",
}
