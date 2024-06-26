import uuid
from typing import Callable

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_change_username_successfully(
    async_client: AsyncClient,
    create_user_in_database: Callable,
    get_user_from_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    request_data: dict = {"username": "new_username"}
    response: Response = await async_client.patch(
        "/api/v1/user/change-username",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["username"] == request_data["username"]
    assert response_data["email"] == user_data["email"]

    user = get_user_from_database(user_data["email"])
    assert user["username"] == request_data["username"]


async def test_change_username_without_auth(
    async_client: AsyncClient,
):
    request_data: dict = {"username": "new_username"}
    response: Response = await async_client.patch(
        "/api/v1/user/change-username",
        json=request_data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_change_username_when_user_is_inactive(
    async_client: AsyncClient,
    create_user_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": False,
    }
    create_user_in_database(**user_data)

    request_data: dict = {"username": "new_username"}
    response: Response = await async_client.patch(
        "/api/v1/user/change-username",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    "data_for_username_change, expected_result",
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
                        "loc": ["body", "username"],
                        "msg": "Field required",
                        "input": {},
                    }
                ]
            },
        ),
        (
            {"username": ""},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, Incorrect username length",
                        "input": "",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {"username": "@"},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, The username contains incorrect symbols",
                        "input": "@",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {"username": "0123456789012345678901"},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, Incorrect username length",
                        "input": "0123456789012345678901",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
    ],
)
async def test_change_username_negative(
    async_client: AsyncClient,
    create_user_in_database: Callable,
    data_for_username_change: dict,
    expected_result: dict,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.patch(
        "/api/v1/user/change-username",
        json=data_for_username_change,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result
