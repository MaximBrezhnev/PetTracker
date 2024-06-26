import uuid
from typing import Callable
from unittest.mock import patch

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.email import EmailService
from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_reset_password_successfully(
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

        request_data: dict = {"email": "some_email@email.ru"}

        response: Response = await async_client.post(
            "/api/v1/user/auth/reset-password",
            json=request_data,
            headers=create_test_auth_headers_for_user(user_data["email"]),
        )

        assert response.status_code == status.HTTP_200_OK
        mock_send_email.assert_awaited_once_with(
            email=[
                request_data["email"],
            ],
            subject="Письмо для сброса пароля в PetTracker",
            template_name="password_reset_confirmation.html",
        )


@pytest.mark.parametrize(
    "data_for_password_reset, expected_result",
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
async def test_reset_password_negative(
    async_client: AsyncClient, data_for_password_reset: dict, expected_result: dict
):
    response: Response = await async_client.post(
        "/api/v1/user/auth/reset-password", json=data_for_password_reset
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result
