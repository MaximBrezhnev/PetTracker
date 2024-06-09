import uuid

import pytest
from httpx import AsyncClient
from fastapi import status

from src.user.services.auth_services import get_password_hash
from tests.conftest import create_test_auth_headers_for_user


async def test_change_password_successfully(
        create_user_in_database,
        async_client: AsyncClient,
        get_user_from_database
):
    old_hashed_password = get_password_hash("1234")
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": old_hashed_password,
        "is_active": True,
        "is_admin": False,
    }
    create_user_in_database(**user_data)

    request_data = {
        "old_password": "1234",
        "password1": "12345",
        "password2": "12345"
    }

    response = await async_client.patch(
        "api/v1/user/change-password",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]


async def test_change_password_old_password_is_incorrect(
        async_client: AsyncClient,
        create_user_in_database,
        get_user_from_database
):
    old_hashed_password = get_password_hash("1234")
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": old_hashed_password,
        "is_active": True,
        "is_admin": False,
    }
    create_user_in_database(**user_data)

    request_data = {
        "old_password": "1233",
        "password1": "12345",
        "password2": "12345"
    }

    response = await async_client.patch(
        "api/v1/user/change-password",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user = get_user_from_database(user_data["email"])
    assert user["hashed_password"] == old_hashed_password


async def test_change_password_when_user_is_inactive(
        async_client: AsyncClient,
        create_user_in_database,
        get_user_from_database
):
    old_hashed_password = get_password_hash("1234")
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": old_hashed_password,
        "is_active": False,
        "is_admin": False,
    }
    create_user_in_database(**user_data)

    request_data = {
        "old_password": "1234",
        "password1": "12345",
        "password2": "12345"
    }
    response = await async_client.patch(
        "api/v1/user/change-password",
        json=request_data,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    user = get_user_from_database(user_data["email"])
    assert user["hashed_password"] == old_hashed_password


async def test_change_password_user_does_no_auth(
        async_client: AsyncClient,

):
    request_data = {
        "old_password": "1234",
        "password1": "12345",
        "password2": "12345"
    }
    response = await async_client.patch(
        "api/v1/user/change-password",
        json=request_data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    "data_for_password_change, expected_result",
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
                            "old_password"
                        ],
                        "msg": "Field required",
                        "input": {}
                    },
                    {
                        "type": "missing",
                        "loc": [
                            "body",
                            "password1"
                        ],
                        "msg": "Field required",
                        "input": {}
                    },
                    {
                        "type": "missing",
                        "loc": [
                            "body",
                            "password2"
                        ],
                        "msg": "Field required",
                        "input": {}
                    }
                ]
            }
        ),
        (
            {
                "password1": "1234",
                "password2": "1234"
            },
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": [
                            "body",
                            "old_password"
                        ],
                        "msg": "Field required",
                        "input": {
                            "password1": "1234",
                            "password2": "1234"
                        }
                    }
                ]
            }
        ),
        (
            {
                "old_password": "1234",
                "password1": "12345",
                "password2": "123456"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body"
                        ],
                        "msg": "Value error, The passwords do not match",
                        "input": {
                            "old_password": "1234",
                            "password1": "12345",
                            "password2": "123456"
                        },
                        "ctx": {
                            "error": {}
                        }
                    }
                ]
            }
        ),
        (
            {
                "old_password": "1234",
                "password1": "123",
                "password2": "123"
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": [
                            "body",
                            "password1"
                        ],
                        "msg": "Value error, The password is weak",
                        "input": "123",
                        "ctx": {
                            "error": {}
                        }
                    }
                ]
            }
        )
    ]

)
async def test_change_password_negative(
        data_for_password_change,
        expected_result,
        create_user_in_database,
        async_client: AsyncClient,
        get_user_from_database
):
    old_hashed_password = get_password_hash("1234")
    user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": old_hashed_password,
        "is_active": True,
        "is_admin": False,
    }
    create_user_in_database(**user_data)

    response = await async_client.patch(
        "api/v1/user/change-password",
        json=data_for_password_change,
        headers=create_test_auth_headers_for_user(user_data["email"])
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_result

    user = get_user_from_database(email=user_data["email"])

    assert user["hashed_password"] == old_hashed_password












