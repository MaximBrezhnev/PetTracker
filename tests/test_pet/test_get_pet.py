from datetime import datetime
from datetime import timedelta
from typing import Callable
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_get_pet_without_events(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
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

    response: Response = await async_client.get(
        f'/api/v1/pet/?pet_id={pet_data["pet_id"]}',
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["pet_id"] == pet_data["pet_id"]
    assert response_data["name"] == pet_data["name"]
    assert response_data["species"] == pet_data["species"]
    assert response_data["breed"] == pet_data["breed"]
    assert response_data["gender"] == pet_data["gender"]
    assert response_data["weight"] == pet_data["weight"]
    assert response_data["events"] == []


async def test_get_pet_with_events_one_event(
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
        "is_happened": False,
    }
    create_event_in_database(**event_data)

    response: Response = await async_client.get(
        f'/api/v1/pet/?pet_id={pet_data["pet_id"]}',
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["pet_id"] == pet_data["pet_id"]
    assert response_data["name"] == pet_data["name"]
    assert response_data["species"] == pet_data["species"]
    assert response_data["breed"] == pet_data["breed"]
    assert response_data["gender"] == pet_data["gender"]
    assert response_data["weight"] == pet_data["weight"]

    assert len(response_data["events"]) == 1
    event: dict = response_data["events"][0]
    assert event["event_id"] == event_data["event_id"]
    assert event["title"] == event_data["title"]
    assert event.get("content", None) is None
    assert event["year"] == event_data["scheduled_at"].year
    assert event["month"] == event_data["scheduled_at"].month
    assert event["day"] == event_data["scheduled_at"].day
    assert event["hour"] == event_data["scheduled_at"].hour
    assert event["minute"] == event_data["scheduled_at"].minute
    assert event["is_happened"] == event_data["is_happened"]


async def test_get_pet_with_events_several_events(
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

    first_event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=5),
        "pet_id": pet_data["pet_id"],
        "is_happened": False,
    }
    create_event_in_database(**first_event_data)

    second_event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=10),
        "pet_id": pet_data["pet_id"],
        "is_happened": False,
    }
    create_event_in_database(**second_event_data)

    response: Response = await async_client.get(
        f'/api/v1/pet/?pet_id={pet_data["pet_id"]}',
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["pet_id"] == pet_data["pet_id"]
    assert response_data["name"] == pet_data["name"]
    assert response_data["species"] == pet_data["species"]
    assert response_data["breed"] == pet_data["breed"]
    assert response_data["gender"] == pet_data["gender"]
    assert response_data["weight"] == pet_data["weight"]

    assert len(response_data["events"]) == 2

    event1 = response_data["events"][1]
    event2 = response_data["events"][0]

    assert event1["event_id"] == first_event_data["event_id"]
    assert event1["title"] == first_event_data["title"]
    assert event1.get("content", None) is None
    assert event1["year"] == first_event_data["scheduled_at"].year
    assert event1["month"] == first_event_data["scheduled_at"].month
    assert event1["day"] == first_event_data["scheduled_at"].day
    assert event1["hour"] == first_event_data["scheduled_at"].hour
    assert event1["minute"] == first_event_data["scheduled_at"].minute
    assert event1["is_happened"] == first_event_data["is_happened"]

    assert event2["event_id"] == second_event_data["event_id"]
    assert event2["title"] == second_event_data["title"]
    assert event2.get("content", None) is None
    assert event2["year"] == second_event_data["scheduled_at"].year
    assert event2["month"] == second_event_data["scheduled_at"].month
    assert event2["day"] == second_event_data["scheduled_at"].day
    assert event2["hour"] == second_event_data["scheduled_at"].hour
    assert event2["minute"] == second_event_data["scheduled_at"].minute
    assert event2["is_happened"] == second_event_data["is_happened"]


async def test_get_pet_when_other_events_exist(
    create_pet_in_database: Callable,
    create_user_in_database: Callable,
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

    another_pet_data = {
        "pet_id": str(uuid4()),
        "name": "Another name",
        "species": "Cat",
        "breed": "Another breed",
        "weight": 15,
        "owner_id": user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**another_pet_data)

    event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=5),
        "pet_id": another_pet_data["pet_id"],
        "is_happened": False,
    }
    create_event_in_database(**event_data)

    response: Response = await async_client.get(
        f'/api/v1/pet/?pet_id={pet_data["pet_id"]}',
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["pet_id"] == pet_data["pet_id"]
    assert response_data["name"] == pet_data["name"]
    assert response_data["species"] == pet_data["species"]
    assert response_data["breed"] == pet_data["breed"]
    assert response_data["gender"] == pet_data["gender"]
    assert response_data["weight"] == pet_data["weight"]

    assert response_data["events"] == []


async def test_get_pet_incorrect_uuid(
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
        "/api/v1/pet/?pet_id=incorrect_id",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "pet_id"],
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


async def test_get_pet_incorrect_user(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
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
        "owner_id": user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**pet_data)

    response: Response = await async_client.get(
        f"/api/v1/pet/?pet_id={pet_data['pet_id']}",
        headers=create_test_auth_headers_for_user(another_user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Pet with this id not found"}


async def test_get_pet_does_not_exist(
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
        f"/api/v1/pet/?pet_id={uuid4()}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Pet with this id not found"}


async def test_get_pet_no_auth(async_client: AsyncClient):
    response: Response = await async_client.get(
        f"/api/v1/pet/?pet_id={uuid4()}",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_get_pet_inactive_user(
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

    response: Response = await async_client.get(
        f"/api/v1/pet/?pet_id={uuid4()}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}
