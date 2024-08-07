import uuid
from typing import Callable

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_token_for_email_confirmation


async def test_change_password_on_reset_successfully(
    async_client: AsyncClient,
    create_user_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    request_data: dict = {
        "token": create_test_token_for_email_confirmation(user_data["email"]),
        "password1": "1234",
        "password2": "1234",
    }

    response: Response = await async_client.patch(
        "/api/v1/user/auth/reset-password/confirmation",
        json=request_data,
    )

    assert response.status_code == status.HTTP_200_OK


async def test_change_password_on_reset_incorrect_token(
    async_client: AsyncClient, create_user_in_database: Callable
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    request_data: dict = {
        "token": create_test_token_for_email_confirmation(user_data["email"]) + "123",
        "password1": "1234",
        "password2": "1234",
    }

    response: Response = await async_client.patch(
        "/api/v1/user/auth/reset-password/confirmation",
        json=request_data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_change_password_on_reset_when_user_does_not_exist(
    async_client: AsyncClient, create_user_in_database: Callable
):
    request_data: dict = {
        "token": create_test_token_for_email_confirmation("some_email@mail.ru"),
        "password1": "1234",
        "password2": "1234",
    }

    response: Response = await async_client.patch(
        "/api/v1/user/auth/reset-password/confirmation",
        json=request_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_change_password_on_reset_when_user_is_inactive(
    async_client: AsyncClient, create_user_in_database: Callable
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": False,
    }
    create_user_in_database(**user_data)

    request_data: dict = {
        "token": create_test_token_for_email_confirmation(user_data["email"]),
        "password1": "1234",
        "password2": "1234",
    }

    response: Response = await async_client.patch(
        "/api/v1/user/auth/reset-password/confirmation",
        json=request_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "data, expected_result",
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
                        "loc": ["body", "token"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password1"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password2"],
                        "msg": "Field required",
                        "input": {},
                    },
                ]
            },
        ),
        (
            {"password1": "1234", "password2": "1234"},
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "token"],
                        "msg": "Field required",
                        "input": {"password1": "1234", "password2": "1234"},
                    }
                ]
            },
        ),
        (
            {"token": "some token", "password1": "123", "password2": "123"},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "password1"],
                        "msg": "Value error, The password is weak",
                        "input": "123",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {"token": "some token", "password1": "1234", "password2": "12345"},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": "Value error, The passwords do not match",
                        "input": {
                            "token": "some token",
                            "password1": "1234",
                            "password2": "12345",
                        },
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
    ],
)
async def test_change_password_on_reset_negative(
    async_client: AsyncClient, data: dict, expected_result: dict
):
    response: Response = await async_client.patch(
        "/api/v1/user/auth/reset-password/confirmation", json=data
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result
