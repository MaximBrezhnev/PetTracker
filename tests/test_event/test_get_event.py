from datetime import datetime
from datetime import timedelta
from typing import Callable
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_get_event_successfully(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    create_event_in_database: Callable,
    async_client: AsyncClient,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**pet_data)

    event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=5),
        "pet_id": pet_data["pet_id"],
        "is_happened": True,
    }
    create_event_in_database(**event_data)

    response: Response = await async_client.get(
        f"/api/v1/event/?event_id={event_data['event_id']}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["event_id"] == event_data["event_id"]
    assert response_data["title"] == event_data["title"]
    assert response_data["content"] == event_data["content"]
    assert response_data["pet_id"] == event_data["pet_id"]
    assert response_data["is_happened"] == event_data["is_happened"]
    assert response_data["year"] == event_data["scheduled_at"].year
    assert response_data["month"] == event_data["scheduled_at"].month
    assert response_data["day"] == event_data["scheduled_at"].day
    assert response_data["hour"] == event_data["scheduled_at"].hour
    assert response_data["minute"] == event_data["scheduled_at"].minute


async def test_get_event_incorrect_event_id(
    create_user_in_database: Callable, async_client: AsyncClient
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.get(
        "/api/v1/event/?event_id=incorrect_id",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "event_id"],
                "msg": "Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` "
                "followed by [0-9a-fA-F-], found `i` at 1",
                "input": "incorrect_id",
                "ctx": {
                    "error": "invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], "
                    "found `i` at 1"
                },
            }
        ]
    }


async def test_get_event_no_auth(async_client: AsyncClient):
    response: Response = await async_client.post(
        f"/api/v1/event/?event_id={uuid4()}", json={}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_get_event_inactive_user(
    create_user_in_database: Callable, async_client: AsyncClient
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": False,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.post(
        f"/api/v1/event/?event_id={uuid4()}",
        json={},
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


async def test_get_event_another_users_pets_event(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    async_client: AsyncClient,
    create_event_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    another_user_data: dict = {
        "user_id": str(uuid4()),
        "username": "another_username",
        "email": "another_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**another_user_data)

    pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": another_user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**pet_data)

    event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=5),
        "pet_id": pet_data["pet_id"],
        "is_happened": True,
    }
    create_event_in_database(**event_data)

    response: Response = await async_client.get(
        f"/api/v1/event/?event_id={event_data['event_id']}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Event with this id belonging to the current user does not exist"
    }


async def test_get_event_not_found(
    create_user_in_database: Callable, async_client: AsyncClient
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.get(
        f"/api/v1/event/?event_id={uuid4()}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Event with this id belonging to the current user does not exist"
    }
