"""Application wiring: metadata, docs endpoints and the OpenAPI schema."""

from fastapi import FastAPI
from httpx import AsyncClient

from app.core import openapi
from app.core.config import settings


def test_app_metadata_comes_from_settings(app: FastAPI) -> None:
    assert app.title == settings.app_name
    assert app.version == settings.api_version
    assert app.description == openapi.DESCRIPTION


async def test_every_route_is_mounted(client: AsyncClient) -> None:
    """Reachability, not introspection — included routers resolve lazily."""
    for path in ("/", "/health"):
        assert (await client.get(path)).status_code != 404, path


async def test_openapi_schema_is_valid_and_documents_the_routes(
    client: AsyncClient,
) -> None:
    response = await client.get(settings.openapi_url)

    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == settings.app_name
    assert schema["info"]["version"] == settings.api_version
    assert set(schema["paths"]) >= {"/", "/health"}


async def test_health_documents_both_status_codes(client: AsyncClient) -> None:
    responses = (await client.get(settings.openapi_url)).json()["paths"]["/health"]["get"][
        "responses"
    ]

    assert {"200", "503"} <= set(responses)


async def test_openapi_tags_are_all_described(client: AsyncClient) -> None:
    """Every tag used by a route should render as a described group in Swagger."""
    schema = (await client.get(settings.openapi_url)).json()
    described = {tag["name"] for tag in schema.get("tags", [])}
    used = {
        tag
        for path in schema["paths"].values()
        for operation in path.values()
        for tag in operation.get("tags", [])
    }

    assert used <= described, f"undocumented tags: {sorted(used - described)}"


async def test_docs_endpoints_are_served(client: AsyncClient) -> None:
    for url in (settings.docs_url, settings.redoc_url):
        response = await client.get(url)
        assert response.status_code == 200, url
        assert "text/html" in response.headers["content-type"]


async def test_unknown_path_is_404(client: AsyncClient) -> None:
    assert (await client.get("/does-not-exist")).status_code == 404
