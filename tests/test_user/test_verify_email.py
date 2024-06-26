import uuid
from typing import Callable

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from tests.conftest import create_test_token_for_email_confirmation


async def test_verify_email_with_correct_token(
    async_client: AsyncClient,
    create_user_in_database: Callable,
    get_user_from_database: Callable,
):
    user_in_database: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": False,
    }
    create_user_in_database(**user_in_database)
    token: str = create_test_token_for_email_confirmation(
        user_in_database["email"], None
    )

    response: Response = await async_client.patch(
        f"/api/v1/user/verification?token={token}"
    )
    assert response.status_code == status.HTTP_200_OK
    user_data: dict = get_user_from_database(user_in_database["email"])
    assert user_data["is_active"] is True


async def test_verify_email_with_incorrect_token(
    async_client: AsyncClient,
    create_user_in_database: Callable,
    get_user_from_database: Callable,
):
    user_in_database: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": False,
    }
    create_user_in_database(**user_in_database)
    token: str = (
        create_test_token_for_email_confirmation(user_in_database["email"], None)
        + "something"
    )

    response: Response = await async_client.patch(
        f"/api/v1/user/verification?token={token}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user_data: dict = get_user_from_database(user_in_database["email"])
    assert user_data["is_active"] is False
