import uuid

import pytest
from httpx import AsyncClient
from fastapi import status

from src.user.services.auth_services import get_password_hash
from tests.conftest import create_test_auth_headers_for_user


async def test_reset_password_successfully(
        async_client: AsyncClient,
        create_user_in_database
):
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": get_password_hash("1234"),
        "is_active": True,
        "is_admin": False,
    }
    create_user_in_database(**user_data)

    # проверка, что отправилась почта
    request_data = {
        "email": "some_email@email.ru"
    }

    response = await async_client.post(
        "/api/v1/user/auth/reset-password",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "data_for_password_reset, expected_result",
    [
        (
            None,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": [
                            "body"
                        ],
                        "msg": "Field required",
                        "input": None
                    }
                ]
            }
        ),
        (
            {},
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": [
                            "body",
                            "email"
                        ],
                        "msg": "Field required",
                        "input": {}
                    }
                ]
            }
        ),
        (
            {"email": "email_mail.ru"},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body",
                            "email"
                        ],
                        "msg": "value is not a valid email address: "
                               "The email address is not valid. It must have exactly one @-sign.",
                        "input": "email_mail.ru",
                        "ctx": {
                            "reason": "The email address is not valid. It must have exactly one @-sign."
                        }
                    }
                ]
            }
        )
    ]
)
async def test_reset_password_negative(
        async_client: AsyncClient,
        data_for_password_reset,
        expected_result
):
    response = await async_client.post(
        "/api/v1/user/auth/reset-password",
        json=data_for_password_reset
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result



