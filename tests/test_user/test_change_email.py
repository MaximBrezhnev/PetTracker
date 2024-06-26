import uuid
from typing import Callable
from unittest.mock import patch

import pytest
from aiosmtplib import SMTPRecipientsRefused
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.models import User
from src.user.services.email import EmailService
from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_change_email_successfully(
    async_client: AsyncClient, create_user_in_database: Callable
):
    with patch.object(EmailService, "send_email") as mock_send_email:

        user_data: dict = {
            "user_id": str(uuid.uuid4()),
            "username": "some_username",
            "email": "some_email@email.ru",
            "hashed_password": Hasher().get_password_hash("1234"),
            "is_active": True,
        }

        create_user_in_database(**user_data)

        request_data: dict = {"email": "new_email@mail.ru"}

        response: Response = await async_client.patch(
            "/api/v1/user/change-email",
            json=request_data,
            headers=create_test_auth_headers_for_user(email=user_data["email"]),
        )

        assert response.status_code == status.HTTP_200_OK

        mock_send_email.assert_awaited_once_with(
            email=[
                request_data["email"],
            ],
            subject="Письмо для подтверждения смены электронной почты в " "PetTracker",
            template_name="email_change_confirmation.html",
            instance=User(**user_data),
        )


async def test_change_email_when_it_is_already_in_use(
    create_user_in_database: Callable,
    async_client: AsyncClient,
):
    with patch.object(EmailService, "send_email") as mock_send_email:

        user_data: dict = {
            "user_id": str(uuid.uuid4()),
            "username": "some_username",
            "email": "some_email@email.ru",
            "hashed_password": Hasher().get_password_hash("1234"),
            "is_active": True,
        }

        create_user_in_database(**user_data)

        request_data: dict = {"email": "some_email@email.ru"}

        response: Response = await async_client.patch(
            "/api/v1/user/change-email",
            json=request_data,
            headers=create_test_auth_headers_for_user(email=user_data["email"]),
        )

        assert response.status_code == status.HTTP_409_CONFLICT

        mock_send_email.assert_not_awaited()


async def test_change_email_when_user_is_inactive(
    async_client: AsyncClient, create_user_in_database: Callable
):
    with (patch.object(EmailService, "send_email") as mock_send_email):

        user_data: dict = {
            "user_id": str(uuid.uuid4()),
            "username": "some_username",
            "email": "some_email@email.ru",
            "hashed_password": Hasher().get_password_hash("1234"),
            "is_active": False,
        }

        create_user_in_database(**user_data)

        request_data: dict = {"email": "some_email@email.ru"}

        response: Response = await async_client.patch(
            "/api/v1/user/change-email",
            json=request_data,
            headers=create_test_auth_headers_for_user(email=user_data["email"]),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        mock_send_email.assert_not_awaited()


async def test_change_email_when_no_auth(
    async_client: AsyncClient,
):
    with patch.object(EmailService, "send_email") as mock_send_email:
        request_data: dict = {"email": "some_email@email.ru"}

        response: Response = await async_client.patch(
            "/api/v1/user/change-email",
            json=request_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        mock_send_email.assert_not_awaited()


async def test_change_email_when_cannot_send_email(
    create_user_in_database: Callable,
    async_client: AsyncClient,
):
    with patch.object(EmailService, "send_email") as mock_send_email:
        user_data: dict = {
            "user_id": str(uuid.uuid4()),
            "username": "some_username",
            "email": "some_email@email.ru",
            "hashed_password": Hasher().get_password_hash("1234"),
            "is_active": True,
        }
        create_user_in_database(**user_data)

        request_data: dict = {"email": "new_email@email.ru"}
        mock_send_email.side_effect = SMTPRecipientsRefused(
            recipients=request_data["email"]
        )

        response: Response = await async_client.patch(
            "/api/v1/user/change-email",
            json=request_data,
            headers=create_test_auth_headers_for_user(email=user_data["email"]),
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {"detail": "Cannot send email"}


@pytest.mark.parametrize(
    "data_for_email_change, expected_result",
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
                        "loc": ["body", "email"],
                        "msg": "Field required",
                        "input": {},
                    }
                ]
            },
        ),
        (
            {"email": "email_mail.ru"},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: "
                        "The email address is not valid. It must have exactly one @-sign.",
                        "input": "email_mail.ru",
                        "ctx": {
                            "reason": "The email address is not valid. It must have exactly one @-sign."
                        },
                    }
                ]
            },
        ),
    ],
)
async def test_change_email_negative(
    data_for_email_change: dict,
    expected_result: dict,
    create_user_in_database: Callable,
    async_client: AsyncClient,
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
        "/api/v1/user/change-email",
        json=data_for_email_change,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result
