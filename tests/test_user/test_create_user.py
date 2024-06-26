import uuid
from typing import Callable
from unittest.mock import patch

import pytest
from aiosmtplib import SMTPRecipientsRefused
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.email import EmailService
from tests.conftest import create_test_auth_headers_for_user


async def test_create_user_user_does_not_exist(
    async_client: AsyncClient,
    get_user_from_database: Callable,
):
    user_data: dict = {
        "username": "some username",
        "email": "some_emailftgnbxtdgfbcf@email.ru",
        "password1": "1234",
        "password2": "1234",
    }
    response: Response = await async_client.post("/api/v1/user/", json=user_data)

    assert response.status_code == status.HTTP_200_OK
    created_user_data: dict = get_user_from_database(user_data["email"])
    assert created_user_data["username"] == user_data["username"]
    assert created_user_data["email"] == user_data["email"]
    assert created_user_data["is_active"] is False


@pytest.mark.parametrize(
    "username, new_username, result_username",
    [
        ("some_username", "some_username", "some_username"),
        ("some_username", "new_username", "new_username"),
    ],
)
async def test_create_user_inactive_user_exists(
    async_client: AsyncClient,
    get_user_from_database: Callable,
    create_user_in_database: Callable,
    username: str,
    new_username: str,
    result_username: str,
):
    inactive_user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": False,
    }
    new_user_data: dict = {
        "username": new_username,
        "email": "some_email@email.ru",
        "password1": "1234",
        "password2": "1234",
    }
    create_user_in_database(**inactive_user_data)
    response: Response = await async_client.post("/api/v1/user/", json=new_user_data)

    assert response.status_code == status.HTTP_200_OK

    created_user_data: dict = get_user_from_database(new_user_data["email"])
    assert str(created_user_data["user_id"]) == inactive_user_data["user_id"]
    assert created_user_data["username"] == result_username
    assert created_user_data["email"] == inactive_user_data["email"]
    assert created_user_data["is_active"] is False


async def test_create_user_active_user_exists(
    async_client: AsyncClient,
    get_user_from_database: Callable,
    create_user_in_database: Callable,
):
    old_user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "username1",
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": True,
    }
    new_user_data: dict = {
        "username": "username2",
        "email": "some_email@email.ru",
        "password1": "1234",
        "password2": "1234",
    }
    create_user_in_database(**old_user_data)
    response: Response = await async_client.post("/api/v1/user/", json=new_user_data)

    assert response.status_code == status.HTTP_409_CONFLICT

    old_user_data_after_request: dict = get_user_from_database(old_user_data["email"])
    assert old_user_data_after_request["user_id"] == old_user_data["user_id"]
    assert old_user_data_after_request["username"] == old_user_data["username"]
    assert old_user_data_after_request["email"] == old_user_data["email"]
    assert old_user_data_after_request["is_active"] is True


async def test_create_user_cannot_send_email(
    create_user_in_database: Callable,
    async_client: AsyncClient,
):
    with patch.object(EmailService, "send_email") as mock_send_email:
        user_data: dict = {
            "username": "some username",
            "email": "some_emailftgnbxtdgfbcf@email.ru",
            "password1": "1234",
            "password2": "1234",
        }

        mock_send_email.side_effect = SMTPRecipientsRefused(
            recipients=user_data["email"]
        )

        response: Response = await async_client.post(
            "/api/v1/user/",
            json=user_data,
            headers=create_test_auth_headers_for_user(email=user_data["email"]),
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {"detail": "Cannot send email"}


async def test_create_user_username_duplicate(
    async_client: AsyncClient,
    get_user_from_database: Callable,
    create_user_in_database: Callable,
):
    old_user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": True,
    }
    new_user_data: dict = {
        "username": "some_username",
        "email": "another_email@email.ru",
        "password1": "1234",
        "password2": "1234",
    }
    create_user_in_database(**old_user_data)
    response: Response = await async_client.post("/api/v1/user/", json=new_user_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    old_user_data_after_request: dict = get_user_from_database(old_user_data["email"])
    assert old_user_data_after_request["user_id"] == old_user_data["user_id"]
    assert old_user_data_after_request["username"] == old_user_data["username"]
    assert old_user_data_after_request["email"] == old_user_data["email"]
    assert old_user_data_after_request["is_active"] is True

    new_user_data_afet_request = get_user_from_database(new_user_data["email"])
    assert new_user_data_afet_request == {}


@pytest.mark.parametrize(
    "user_data_for_creation, expected_detail",
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
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "email"],
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
            {
                "username": "@username",
                "email": "some_email@mail.ru",
                "password1": "1234",
                "password2": "1234",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, The username contains incorrect symbols",
                        "input": "@username",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "username": "",
                "email": "some_email@mail.ru",
                "password1": "1234",
                "password2": "1234",
            },
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
            {
                "username": "123456789012345678901",
                "email": "some_email@mail.ru",
                "password1": "1234",
                "password2": "1234",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "username"],
                        "msg": "Value error, Incorrect username length",
                        "input": "123456789012345678901",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "username": "some_username",
                "email": "some_email@mail.ru",
                "password1": "134",
                "password2": "134",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "password1"],
                        "msg": "Value error, The password is weak",
                        "input": "134",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "username": "some_username",
                "email": "some_email@mail.ru",
                "password1": "12334",
                "password2": "1234",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": "Value error, The passwords do not match",
                        "input": {
                            "username": "some_username",
                            "email": "some_email@mail.ru",
                            "password1": "12334",
                            "password2": "1234",
                        },
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "username": "some_username",
                "email": "some_emailmail.ru",
                "password1": "1234",
                "password2": "1234",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: The email address is not valid. "
                        "It must have exactly one @-sign.",
                        "input": "some_emailmail.ru",
                        "ctx": {
                            "reason": "The email address is not valid. It must have exactly one @-sign."
                        },
                    }
                ]
            },
        ),
    ],
)
async def test_create_user_negative(
    async_client: AsyncClient, user_data_for_creation: dict, expected_detail: dict
):
    response: Response = await async_client.post(
        "/api/v1/user/", json=user_data_for_creation
    )
    assert response.status_code == 422
    assert response.json() == expected_detail
