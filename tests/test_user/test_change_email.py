import uuid

import pytest
from httpx import AsyncClient
from fastapi import status

from src.user.services.auth_services import get_password_hash
from tests.conftest import create_test_auth_headers_for_user


async def test_change_email_successfully(
        async_client: AsyncClient,
        create_user_in_database
):
    # Должна быть также проверка почты
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": get_password_hash("1234"),
        "is_active": True,
        "is_admin": False,
    }

    create_user_in_database(**user_data)

    request_data = {
        "email": "new_email@mail.ru"
    }

    response = await async_client.patch(
        "/api/v1/user/change-email",
        json=request_data,
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )

    assert response.status_code == status.HTTP_200_OK


async def test_change_email_when_it_is_already_in_use(
        create_user_in_database,
        async_client: AsyncClient,
):
    # Проверка, что почта не вызвалась
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": get_password_hash("1234"),
        "is_active": True,
        "is_admin": False,
    }

    create_user_in_database(**user_data)

    request_data = {
        "email": "some_email@email.ru"
    }

    response = await async_client.patch(
        "/api/v1/user/change-email",
        json=request_data,
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_change_email_when_user_is_inactive(
        async_client: AsyncClient,
        create_user_in_database
):
    # проверка, что почта не вызвалась
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": get_password_hash("1234"),
        "is_active": False,
        "is_admin": False,
    }

    create_user_in_database(**user_data)

    request_data = {
        "email": "some_email@email.ru"
    }

    response = await async_client.patch(
        "/api/v1/user/change-email",
        json=request_data,
        headers=create_test_auth_headers_for_user(email=user_data["email"])
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_change_email_when_no_auth(
        async_client: AsyncClient,

):
    # проверка, что почта не вызвалась
    request_data = {
        "email": "some_email@email.ru"
    }

    response = await async_client.patch(
        "/api/v1/user/change-email",
        json=request_data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_change_email_when_cannot_send_email():
    pass


@pytest.mark.parametrize(
    "data_for_email_change, expected_result",
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
async def test_change_email_negative(
        data_for_email_change,
        expected_result,
        create_user_in_database,
        async_client: AsyncClient
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

    response = await async_client.patch(
        "/api/v1/user/change-email",
        json=data_for_email_change,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result
