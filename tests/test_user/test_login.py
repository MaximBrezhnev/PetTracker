import uuid
from datetime import timedelta

from httpx import AsyncClient

from src.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from src.user.services.auth_services import create_jwt_token, get_password_hash
from tests.conftest import create_user_in_database

from fastapi import status


async def test_login_when_user_exists(
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

    login_data = {
        "grant_type": None,
        "username": "some_username",
        "password": "1234",
        "scope": None,
        "client_id": None,
        "client_secret": None
    }
    response = await async_client.post(
        "/api/v1/user/auth/login", data=login_data
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["access_token"] == create_jwt_token(
        user_data["email"], timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    assert response_data["refresh_token"] == create_jwt_token(
        user_data["email"], timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    assert response_data["token_type"] == "bearer"


async def test_login_when_user_does_not_exist(async_client: AsyncClient):
    login_data = {
        "grant_type": None,
        "username": "some_username",
        "password": "1234",
        "scope": None,
        "client_id": None,
        "client_secret": None
    }
    response = await async_client.post(
        "/api/v1/user/auth/login", data=login_data
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_login_when_user_is_inactive(
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

    login_data = {
        "grant_type": None,
        "username": "some_username",
        "password": "1234",
        "scope": None,
        "client_id": None,
        "client_secret": None
    }
    response = await async_client.post(
        "/api/v1/user/auth/login", data=login_data
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_login_when_password_is_incorrect(
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

    login_data = {
        "grant_type": None,
        "username": "some_username",
        "password": "12345",
        "scope": None,
        "client_id": None,
        "client_secret": None
    }
    response = await async_client.post(
        "/api/v1/user/auth/login", data=login_data
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
