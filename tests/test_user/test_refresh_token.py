import uuid
from datetime import timedelta

from httpx import AsyncClient
from fastapi import status

from src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from src.user.services.auth_services import get_password_hash, create_jwt_token
from tests.conftest import create_user_in_database, create_test_auth_headers_for_user


async def test_refresh_token(
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

    response = await async_client.post(
        "/api/v1/user/auth/refresh-token",
        headers=create_test_auth_headers_for_user(user_data["email"])
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["access_token"] == create_jwt_token(
        user_data["email"],
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    assert response_data["refresh_token"] is None
    assert response_data["token_type"] == "bearer"


async def test_refresh_token_when_user_is_inactive(
        async_client: AsyncClient,
        create_user_in_database
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

    response = await async_client.post(
        "/api/v1/user/auth/refresh-token",
        headers=create_test_auth_headers_for_user(user_data["email"])
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_token_when_token_is_incorrect(
        async_client: AsyncClient,
        create_user_in_database
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

    response = await async_client.post(
        "/api/v1/user/auth/refresh-token",
        headers=create_test_auth_headers_for_user(user_data["email"]+"1234")
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED





