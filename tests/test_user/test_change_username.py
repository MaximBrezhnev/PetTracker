import uuid

import pytest
from httpx import AsyncClient
from fastapi import status

from src.user.services.auth_services import get_password_hash
from tests.conftest import create_user_in_database, create_test_auth_headers_for_user, get_user_from_database


async def test_change_username_successful(
        async_client: AsyncClient,
        create_user_in_database,
        get_user_from_database
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

    request_data = {
        "username": "new_username"
    }
    response = await async_client.patch(
        "/api/v1/user/change-username",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["username"] == request_data["username"]
    assert response_data["email"] == user_data["email"]

    user = get_user_from_database(user_data["email"])
    assert user["username"] == request_data["username"]


async def test_change_username_without_auth(
        async_client: AsyncClient,
):
    request_data = {
        "username": "new_username"
    }
    response = await async_client.patch(
        "/api/v1/user/change-username",
        json=request_data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_change_username_when_user_is_inactive(
        async_client: AsyncClient,
        create_user_in_database,
):
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
        "username": "new_username"
    }
    response = await async_client.patch(
        "/api/v1/user/change-username",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"])
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
                            "username"
                        ],
                        "msg": "Field required",
                        "input": {}
                    }
                ]
            }
        ),
        (
            {
                "username": ""
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body",
                            "username"
                        ],
                        "msg": "Value error, Incorrect username length",
                        "input": "",
                        "ctx": {
                            "error": {}
                        }
                    }
                ]
            }
        ),
        (
            {
                "username": "@"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body",
                            "username"
                        ],
                        "msg": "Value error, The username contains incorrect symbols",
                        "input": "@",
                        "ctx": {
                            "error": {}
                        }
                    }
                ]
            }
        ),
        (
            {
                "username": "0123456789012345678901"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body",
                            "username"
                        ],
                        "msg": "Value error, Incorrect username length",
                        "input": "0123456789012345678901",
                        "ctx": {
                            "error": {}
                        }
                    }
                ]
            }
        ),
    ]
)
async def test_change_username_negative(
        async_client: AsyncClient,
        create_user_in_database,
        data_for_username_change,
        expected_result
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
        "/api/v1/user/change-username",
        json=data_for_username_change,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result


