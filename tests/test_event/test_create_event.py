from datetime import datetime
from typing import Callable
from typing import Tuple
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


async def test_create_event_successfully(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
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
            "title": "Some title",
            "content": "Some content",
            "year": datetime.now().year + 1,
            "month": 10,
            "day": 10,
            "hour": 10,
            "minute": 10,
            "timezone": "Europe/Moscow",
            "pet_id": pet_data["pet_id"],
        }

        response: Response = await async_client.post(
            "/api/v1/event/",
            json=event_data,
            headers=create_test_auth_headers_for_user(user_data["email"]),
        )
        response_data: dict = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert response_data["title"] == event_data["title"]
        assert response_data["content"] == event_data["content"]
        assert response_data["year"] == event_data["year"]
        assert response_data["month"] == event_data["month"]
        assert response_data["hour"] == event_data["hour"]
        assert response_data["minute"] == event_data["minute"]
        assert response_data["pet_id"] == event_data["pet_id"]

        created_event: dict = get_event_from_database(event_data["title"])
        assert created_event["content"] == event_data["content"]
        assert created_event["scheduled_at"] == datetime(
            year=event_data["year"],
            month=event_data["month"],
            day=event_data["day"],
            hour=event_data["hour"],
            minute=event_data["minute"],
        )
        assert created_event["is_happened"] is False

        mock_create_task.assert_called_once()


async def test_create_event_successfully_task_sent(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
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
            "title": "Some title",
            "year": datetime.now().year + 1,
            "month": 10,
            "day": 10,
            "hour": 10,
            "minute": 10,
            "timezone": "Europe/Moscow",
            "pet_id": pet_data["pet_id"],
        }

        await async_client.post(
            "/api/v1/event/",
            json=event_data,
            headers=create_test_auth_headers_for_user(user_data["email"]),
        )

        event_data_from_database: dict = get_event_from_database(event_data["title"])
        task: Tuple = get_task_from_database(event_data_from_database["event_id"])
        assert task is not None

        mock_create_task.assert_called_once_with(
            scheduled_at=event_data_from_database["scheduled_at"],
            event=Event(**event_data_from_database),
            user=User(**user_data),
            pet=Pet(**pet_data),
            task_id=UUID(task[0]),
            timezone=event_data["timezone"],
        )


async def test_create_event_no_auth(async_client: AsyncClient):
    response: Response = await async_client.post("/api/v1/event/", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_create_event_inactive_user(
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
        "/api/v1/pet/",
        json={},
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


async def test_create_event_pet_not_found(
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

    event_data: dict = {
        "title": "Some title",
        "content": "Some content",
        "year": datetime.now().year + 1,
        "month": 10,
        "day": 10,
        "hour": 10,
        "minute": 10,
        "timezone": "Europe/Moscow",
        "pet_id": str(uuid4()),
    }

    response: Response = await async_client.post(
        "/api/v1/event/",
        json=event_data,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "User does not own the pet whose event to be created"
    }


async def test_create_event_another_users_pet(
    create_user_in_database: Callable,
    async_client: AsyncClient,
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
        "title": "Some title",
        "content": "Some content",
        "year": datetime.now().year + 1,
        "month": 10,
        "day": 10,
        "hour": 10,
        "minute": 10,
        "timezone": "Europe/Moscow",
        "pet_id": str(uuid4()),
    }

    response: Response = await async_client.post(
        "/api/v1/event/",
        json=event_data,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "User does not own the pet whose event to be created"
    }


@pytest.mark.parametrize(
    "event_data, expected_detail",
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
                        "loc": ["body", "title"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "year"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "month"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "day"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "hour"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "minute"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "timezone"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "pet_id"],
                        "msg": "Field required",
                        "input": {},
                    },
                ]
            },
        ),
        (
            {
                "content": "Some content",
                "year": 2024,
                "month": 10,
                "day": 10,
                "hour": 10,
                "minute": 10,
                "timezone": "Europe/Moscow",
                "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
            },
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "title"],
                        "msg": "Field required",
                        "input": {
                            "content": "Some content",
                            "year": 2024,
                            "month": 10,
                            "day": 10,
                            "hour": 10,
                            "minute": 10,
                            "timezone": "Europe/Moscow",
                            "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
                        },
                    }
                ]
            },
        ),
        (
            {
                "title": "Some title",
                "content": "Some content",
                "year": 2024,
                "month": 11,
                "day": 31,
                "hour": 10,
                "minute": 10,
                "timezone": "Europe/Moscow",
                "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": "Value error, day is out of range for month",
                        "input": {
                            "title": "Some title",
                            "content": "Some content",
                            "year": 2024,
                            "month": 11,
                            "day": 31,
                            "hour": 10,
                            "minute": 10,
                            "timezone": "Europe/Moscow",
                            "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
                        },
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "title": "Some title",
                "content": "Some content",
                "year": 2010,
                "month": 11,
                "day": 30,
                "hour": 10,
                "minute": 10,
                "timezone": "Europe/Moscow",
                "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": "Value error, Date must be greater than the current one by at least a minute",
                        "input": {
                            "title": "Some title",
                            "content": "Some content",
                            "year": 2010,
                            "month": 11,
                            "day": 30,
                            "hour": 10,
                            "minute": 10,
                            "timezone": "Europe/Moscow",
                            "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
                        },
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "title": "",
                "content": "",
                "year": 2010,
                "month": 11,
                "day": 30,
                "hour": 10,
                "minute": 10,
                "timezone": "Europe/Moscow",
                "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
            },
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["body", "title"],
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    },
                    {
                        "type": "string_too_short",
                        "loc": ["body", "content"],
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    },
                ]
            },
        ),
        (
            {
                "title": "Some title",
                "content": "Some content",
                "year": 2024,
                "month": 11,
                "day": 30,
                "hour": 10,
                "minute": 10,
                "timezone": "Invalid timezone",
                "pet_id": "e0c158d6-3009-4032-8f1f-e923bd7b7001",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "timezone"],
                        "msg": "Value error, Provided value is not a valid timezone name",
                        "input": "Invalid timezone",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "title": "Some title",
                "content": "Some content",
                "year": 2024,
                "month": 11,
                "day": 30,
                "hour": 10,
                "minute": 10,
                "timezone": "Europe/Moscow",
                "pet_id": "Incorrect_pet_id",
            },
            {
                "detail": [
                    {
                        "type": "uuid_parsing",
                        "loc": ["body", "pet_id"],
                        "msg": "Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `I` at 1",
                        "input": "Incorrect_pet_id",
                        "ctx": {
                            "error": "invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `I` at 1"
                        },
                    }
                ]
            },
        ),
    ],
)
async def test_create_event_negative(
    event_data: dict,
    expected_detail: dict,
    create_user_in_database: Callable,
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

    response: Response = await async_client.post(
        "/api/v1/event/",
        json=event_data,
        headers=create_test_auth_headers_for_user(email=user_data["email"]),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_detail
