import uuid
from typing import Callable

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from tests.conftest import create_test_auth_headers_for_user


async def test_get_user_when_authenticated(
    create_user_in_database: Callable,
    async_client: AsyncClient,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.get(
        "/api/v1/user/", headers=create_test_auth_headers_for_user(user_data["email"])
    )
    data_from_response: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data_from_response["username"] == user_data["username"]
    assert data_from_response["email"] == user_data["email"]


async def test_get_user_when_not_authenticated(
    async_client: AsyncClient,
):
    response: Response = await async_client.get("/api/v1/user/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
