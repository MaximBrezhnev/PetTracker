from datetime import datetime
from datetime import timedelta
from typing import Callable
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_delete_event_successfully(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    async_client: AsyncClient,
    create_event_in_database: Callable,
    create_task_in_database: Callable,
    get_event_from_database: Callable,
    get_task_from_database: Callable,
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

    task_data: dict = {"task_id": str(uuid4()), "event_id": event_data["event_id"]}
    create_task_in_database(**task_data)

    response: Response = await async_client.delete(
        f"/api/v1/event/?event_id={event_data['event_id']}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": f"Event with id {event_data['event_id']}"
        f" was deleted successfully"
    }

    event_from_database: dict = get_event_from_database(event_data["title"])
    assert event_from_database == {}

    task_record_from_database: None = get_task_from_database(event_data["event_id"])
    assert task_record_from_database is None


async def test_delete_event_not_found(
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

    response: Response = await async_client.delete(
        f"/api/v1/event/?event_id={uuid4()}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Event with this id belonging to the current user does not exist"
    }


async def test_delete_event_no_auth(async_client: AsyncClient):
    response: Response = await async_client.delete(f"/api/v1/event/?event_id={uuid4()}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_delete_event_inactive_user(
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

    response: Response = await async_client.delete(
        f"/api/v1/event/?event_id={uuid4()}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


async def test_delete_event_another_users_event(
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

    response: Response = await async_client.delete(
        f"/api/v1/event/?event_id={event_data['event_id']}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Event with this id belonging to the current " "user does not exist"
    }
