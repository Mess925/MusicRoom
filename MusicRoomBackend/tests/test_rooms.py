"""POST /rooms/{public,private} and POST /rooms/{id}/join."""

import uuid

from httpx import AsyncClient

from app.core.tokens import ACCESS_CODE_LENGTH
from tests.fakes import FakeSession


async def test_create_public_room_returns_an_id_and_no_access_code(client: AsyncClient) -> None:
    response = await client.post("/rooms/public", json={})

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"])  # parses
    assert body["visibility"] == "public"
    assert body["access_code"] is None


async def test_create_private_room_returns_an_id_and_a_generated_access_code(
    client: AsyncClient,
) -> None:
    response = await client.post("/rooms/private", json={"name": "after hours"})

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"])
    assert body["visibility"] == "private"
    code = body["access_code"]
    assert isinstance(code, str)
    assert len(code) == ACCESS_CODE_LENGTH
    assert code.isalnum() and code.isupper()


async def test_two_private_rooms_get_different_codes(client: AsyncClient) -> None:
    first = (await client.post("/rooms/private", json={})).json()["access_code"]
    second = (await client.post("/rooms/private", json={})).json()["access_code"]

    assert first != second


async def test_room_is_persisted(client: AsyncClient, session: FakeSession) -> None:
    await client.post("/rooms/public", json={})

    assert session.commits == 1
    assert len(session._store) == 1


async def test_join_public_room_needs_only_the_id(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/public", json={})).json()["id"]

    response = await client.post(f"/rooms/{room_id}/join")

    assert response.status_code == 200
    assert response.json()["id"] == room_id


async def test_join_private_room_succeeds_with_the_right_code(client: AsyncClient) -> None:
    created = (await client.post("/rooms/private", json={})).json()

    response = await client.post(
        f"/rooms/{created['id']}/join", json={"access_code": created["access_code"]}
    )

    assert response.status_code == 200
    assert response.json()["visibility"] == "private"


async def test_join_private_room_is_403_with_a_wrong_code(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/private", json={})).json()["id"]

    response = await client.post(f"/rooms/{room_id}/join", json={"access_code": "WRONG1"})

    assert response.status_code == 403


async def test_join_private_room_is_403_without_a_code(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/private", json={})).json()["id"]

    response = await client.post(f"/rooms/{room_id}/join")

    assert response.status_code == 403


async def test_join_unknown_room_is_404(client: AsyncClient) -> None:
    response = await client.post(f"/rooms/{uuid.uuid4()}/join")

    assert response.status_code == 404


async def test_join_with_a_non_uuid_id_is_422(client: AsyncClient) -> None:
    response = await client.post("/rooms/not-a-uuid/join")

    assert response.status_code == 422


async def test_delete_public_room_with_its_id_as_the_confirmation_code(
    client: AsyncClient, session: FakeSession
) -> None:
    room_id = (await client.post("/rooms/public", json={})).json()["id"]

    response = await client.request(
        "DELETE", f"/rooms/{room_id}", json={"confirmation_code": room_id}
    )

    assert response.status_code == 204
    assert len(session._store) == 0
    assert (await client.post(f"/rooms/{room_id}/join")).status_code == 404


async def test_delete_private_room_with_its_access_code(client: AsyncClient) -> None:
    created = (await client.post("/rooms/private", json={})).json()

    response = await client.request(
        "DELETE",
        f"/rooms/{created['id']}",
        json={"confirmation_code": created["access_code"]},
    )

    assert response.status_code == 204


async def test_delete_public_room_is_403_with_a_wrong_code(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/public", json={})).json()["id"]

    response = await client.request(
        "DELETE", f"/rooms/{room_id}", json={"confirmation_code": "not-the-id"}
    )

    assert response.status_code == 403


async def test_delete_private_room_is_403_with_the_room_id_instead_of_the_code(
    client: AsyncClient,
) -> None:
    room_id = (await client.post("/rooms/private", json={})).json()["id"]

    response = await client.request(
        "DELETE", f"/rooms/{room_id}", json={"confirmation_code": room_id}
    )

    assert response.status_code == 403


async def test_delete_room_requires_a_confirmation_code(client: AsyncClient) -> None:
    room_id = (await client.post("/rooms/public", json={})).json()["id"]

    response = await client.request("DELETE", f"/rooms/{room_id}", json={})

    assert response.status_code == 422


async def test_delete_unknown_room_is_404(client: AsyncClient) -> None:
    response = await client.request(
        "DELETE", f"/rooms/{uuid.uuid4()}", json={"confirmation_code": "whatever"}
    )

    assert response.status_code == 404
