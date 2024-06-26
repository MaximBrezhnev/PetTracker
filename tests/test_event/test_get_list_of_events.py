from datetime import datetime
from datetime import timedelta
from typing import Callable
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_get_list_of_events_successfully_one_event(
    create_user_in_database: Callable,
    async_client: AsyncClient,
    create_event_in_database: Callable,
    create_pet_in_database: Callable,
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
        "/api/v1/event/list-of-events",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data = response.json()

    assert len(response_data) == 1
    event: dict = response_data[0]
    assert response.status_code == status.HTTP_200_OK
    assert event["event_id"] == event_data["event_id"]
    assert event["title"] == event_data["title"]
    assert event["content"] is None
    assert event["pet_id"] == event_data["pet_id"]
    assert event["is_happened"] == event_data["is_happened"]
    assert event["year"] == event_data["scheduled_at"].year
    assert event["month"] == event_data["scheduled_at"].month
    assert event["day"] == event_data["scheduled_at"].day
    assert event["hour"] == event_data["scheduled_at"].hour
    assert event["minute"] == event_data["scheduled_at"].minute


async def test_get_list_of_events_successfully_two_events(
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
        "is_happened": True,
    }
    create_event_in_database(**first_event_data)

    second_event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=10),
        "pet_id": pet_data["pet_id"],
        "is_happened": True,
    }
    create_event_in_database(**second_event_data)

    response: Response = await async_client.get(
        "/api/v1/event/list-of-events",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data) == 2

    event2 = response_data[0]
    event1 = response_data[1]

    assert event1["event_id"] == first_event_data["event_id"]
    assert event1["title"] == first_event_data["title"]
    assert event1["content"] is None
    assert event1["pet_id"] == first_event_data["pet_id"]
    assert event1["is_happened"] == first_event_data["is_happened"]
    assert event1["year"] == first_event_data["scheduled_at"].year
    assert event1["month"] == first_event_data["scheduled_at"].month
    assert event1["day"] == first_event_data["scheduled_at"].day
    assert event1["hour"] == first_event_data["scheduled_at"].hour
    assert event1["minute"] == first_event_data["scheduled_at"].minute

    assert event2["event_id"] == second_event_data["event_id"]
    assert event2["title"] == second_event_data["title"]
    assert event2["content"] is None
    assert event2["pet_id"] == second_event_data["pet_id"]
    assert event2["is_happened"] == second_event_data["is_happened"]
    assert event2["year"] == second_event_data["scheduled_at"].year
    assert event2["month"] == second_event_data["scheduled_at"].month
    assert event2["day"] == second_event_data["scheduled_at"].day
    assert event2["hour"] == second_event_data["scheduled_at"].hour
    assert event2["minute"] == second_event_data["scheduled_at"].minute


async def test_get_list_of_events_no_auth(async_client: AsyncClient):
    response: Response = await async_client.get(
        "/api/v1/event/list-of-events",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_get_list_of_events_inactive_user(
    create_user_in_database: Callable, async_client: AsyncClient
):
    user_data = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": False,
    }
    create_user_in_database(**user_data)

    response = await async_client.get(
        "/api/v1/event/list-of-events",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


async def test_get_list_of_events_no_events(
    create_user_in_database, async_client: AsyncClient
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
        "/api/v1/event/list-of-events",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "There are no events belonging to the current user"
    }


async def test_get_list_of_events_another_users_event(
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

    another_pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": another_user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**another_pet_data)

    event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=5),
        "pet_id": pet_data["pet_id"],
        "is_happened": True,
    }
    create_event_in_database(**event_data)

    another_event_data: dict = {
        "event_id": str(uuid4()),
        "title": "some title",
        "content": "some content",
        "scheduled_at": datetime.now() + timedelta(minutes=5),
        "pet_id": another_pet_data["pet_id"],
        "is_happened": True,
    }
    create_event_in_database(**another_event_data)

    response: Response = await async_client.get(
        "/api/v1/event/list-of-events",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

    event_from_response: dict = response.json()[0]
    assert event_from_response["event_id"] == event_data["event_id"]
    assert event_from_response["title"] == event_data["title"]
    assert event_from_response["content"] is None
    assert event_from_response["pet_id"] == event_data["pet_id"]
    assert event_from_response["is_happened"] == event_data["is_happened"]
    assert event_from_response["year"] == event_data["scheduled_at"].year
    assert event_from_response["month"] == event_data["scheduled_at"].month
    assert event_from_response["day"] == event_data["scheduled_at"].day
    assert event_from_response["hour"] == event_data["scheduled_at"].hour
    assert event_from_response["minute"] == event_data["scheduled_at"].minute
