from datetime import datetime
from datetime import timedelta
from typing import Callable
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.event.models import Event
from src.event.services.services import EventService
from src.pet.models import Pet
from src.user.models import User
from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_update_event_successfully(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    create_event_in_database: Callable,
    create_task_in_database: Callable,
    async_client: AsyncClient,
    get_event_from_database: Callable,
):
    with patch.object(EventService, "_create_task") as mock_create_task:

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
            "scheduled_at": datetime(
                year=datetime.now().year + 1,
                month=10,
                day=10,
                hour=10,
                minute=10,
            ),
            "pet_id": pet_data["pet_id"],
            "is_happened": False,
        }
        create_event_in_database(**event_data)

        task_data: dict = {"task_id": str(uuid4()), "event_id": event_data["event_id"]}
        create_task_in_database(**task_data)

        event_data_for_update: dict = {
            "title": "New title",
            "year": datetime.now().year + 2,
            "month": 10,
            "day": 10,
            "hour": 10,
            "minute": 10,
            "timezone": "Europe/Moscow",
        }

        response: Response = await async_client.patch(
            f"/api/v1/event/?event_id={event_data['event_id']}",
            json=event_data_for_update,
            headers=create_test_auth_headers_for_user(user_data["email"]),
        )

        response_data: dict = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert response_data["title"] == event_data_for_update["title"]
        assert response_data["content"] == event_data["content"]
        assert response_data["year"] == event_data_for_update["year"]
        assert response_data["month"] == event_data_for_update["month"]
        assert response_data["hour"] == event_data_for_update["hour"]
        assert response_data["minute"] == event_data_for_update["minute"]
        assert response_data["pet_id"] == event_data["pet_id"]

        updated_event: dict = get_event_from_database(event_data_for_update["title"])
        assert updated_event["content"] == event_data["content"]
        assert updated_event["scheduled_at"] == datetime(
            year=event_data_for_update["year"],
            month=event_data_for_update["month"],
            day=event_data_for_update["day"],
            hour=event_data_for_update["hour"],
            minute=event_data_for_update["minute"],
        )
        assert updated_event["is_happened"] is False

        old_event: dict = get_event_from_database(event_data["title"])
        assert old_event == {}

        mock_create_task.assert_called_once()


async def test_update_event_successfully_task_changes(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    create_event_in_database: Callable,
    create_task_in_database: Callable,
    async_client: AsyncClient,
    get_task_from_database: Callable,
    get_event_from_database: Callable,
):
    with patch.object(EventService, "_create_task") as mock_create_task:

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

        task_data: dict = {"task_id": str(uuid4()), "event_id": event_data["event_id"]}
        create_task_in_database(**task_data)

        event_data_for_update: dict = {
            "title": "New title",
            "year": datetime.now().year + 1,
            "month": 10,
            "day": 10,
            "hour": 10,
            "minute": 10,
            "timezone": "Europe/Moscow",
        }

        response: Response = await async_client.patch(
            f"/api/v1/event/?event_id={event_data['event_id']}",
            json=event_data_for_update,
            headers=create_test_auth_headers_for_user(user_data["email"]),
        )

        assert response.status_code == status.HTTP_200_OK
        task_record_from_database: dict = get_task_from_database(event_data["event_id"])
        assert task_record_from_database[1] != task_data["task_id"]

        updated_event: dict = get_event_from_database(event_data_for_update["title"])
        mock_create_task.assert_called_once_with(
            scheduled_at=updated_event["scheduled_at"],
            event=Event(**updated_event),
            user=User(**user_data),
            pet=Pet(**pet_data),
            task_id=UUID(task_record_from_database[0]),
            timezone=event_data_for_update["timezone"],
        )


async def test_update_event_not_found(
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

    event_data_for_update: dict = {"title": "new title", "timezone": "Europe/Moscow"}

    response: Response = await async_client.patch(
        f"/api/v1/event/?event_id={uuid4()}",
        json=event_data_for_update,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Event with this id belonging to the current user does not exist"
    }


async def test_update_event_no_auth(async_client: AsyncClient):
    response: Response = await async_client.patch(
        f"/api/v1/event/?event_id={uuid4()}",
        json={},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_update_event_inactive_user(
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

    response: Response = await async_client.patch(
        f"/api/v1/event/?event_id={uuid4()}",
        json={},
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


async def test_update_event_another_users_event(
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
        "is_happened": False,
    }
    create_event_in_database(**event_data)

    event_data_for_update: dict = {"title": "New title", "timezone": "Europe/Moscow"}

    response: Response = await async_client.patch(
        f"/api/v1/event/?event_id={event_data['event_id']}",
        json=event_data_for_update,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Event with this id belonging to the current user does not exist"
    }


@pytest.mark.parametrize(
    "request_data, expected_result",
    [
        (
            None,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body"],
                        "msg": "Field required",
                        "input": None,
                    }
                ]
            },
        ),
        (
            {},
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "timezone"],
                        "msg": "Field required",
                        "input": {},
                    }
                ]
            },
        ),
        (
            {"title": "new title"},
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "timezone"],
                        "msg": "Field required",
                        "input": {"title": "new title"},
                    }
                ]
            },
        ),
        (
            {"timezone": "Europe/Moscow"},
            {"detail": "At least one parameter must be provided"},
        ),
        (
            {"title": "", "timezone": "Europe/Moscow"},
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["body", "title"],
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    }
                ]
            },
        ),
        (
            {
                "year": 2020,
                "month": 10,
                "day": 12,
                "hour": 10,
                "minute": 2,
                "timezone": "Europe/Moscow",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": "Value error, Date must be greater than the current one by at least a minute",
                        "input": {
                            "year": 2020,
                            "month": 10,
                            "day": 12,
                            "hour": 10,
                            "minute": 2,
                            "timezone": "Europe/Moscow",
                        },
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {"title": "new title", "timezone": "Asia/Moscow"},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "timezone"],
                        "msg": "Value error, Provided value is not a valid timezone name",
                        "input": "Asia/Moscow",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
    ],
)
async def test_update_event_negative(
    request_data: dict,
    expected_result: dict,
    async_client: AsyncClient,
    create_user_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.patch(
        f"/api/v1/event/?event_id={uuid4()}",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result
