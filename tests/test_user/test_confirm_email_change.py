import uuid
from typing import Callable

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.models import User
from src.user.services.hashing import Hasher
from tests.conftest import create_test_token_for_email_confirmation


async def test_confirm_email_change_successfully(
    async_client: AsyncClient,
    get_user_from_database: Callable,
    create_user_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)
    new_email: str = "new_email@mail.ru"
    user: User = User(**user_data)

    token: str = create_test_token_for_email_confirmation(new_email, user)
    response: Response = await async_client.patch(
        f"/api/v1/user/change-email/confirmation?token={token}",
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert response_data["email"] == new_email
    assert response_data["username"] == user_data["username"]

    user_with_new_email: dict = get_user_from_database(new_email)
    assert user_with_new_email != {}
    user_with_old_email: dict = get_user_from_database(user_data["email"])
    assert user_with_old_email == {}


async def test_confirm_email_change_duplicate(
    async_client: AsyncClient,
    get_user_from_database: Callable,
    create_user_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)
    new_email: str = "new_email@email.ru"
    user: User = User(**user_data)

    another_user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "another_username",
        "email": "new_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**another_user_data)

    token: str = create_test_token_for_email_confirmation(new_email, user)
    response: Response = await async_client.patch(
        f"/api/v1/user/change-email/confirmation?token={token}",
    )

    assert response.status_code == status.HTTP_409_CONFLICT

    user_from_database: dict = get_user_from_database(user_data["email"])
    assert user_from_database["email"] == user_data["email"]


async def test_confirm_email_change_incorrect_token(
    async_client: AsyncClient,
    create_user_in_database: Callable,
    get_user_from_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)
    new_email: str = "new_email@email.ru"
    user: User = User(**user_data)

    token: str = create_test_token_for_email_confirmation(new_email, user)
    response: Response = await async_client.patch(
        f"/api/v1/user/change-email/confirmation?token={token}+123",
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_confirm_email_change_user_is_inactive(
    create_user_in_database: Callable, async_client: AsyncClient
):
    user_data: dict = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": False,
    }
    create_user_in_database(**user_data)
    new_email: str = "new_email@email.ru"
    user: User = User(**user_data)

    token: str = create_test_token_for_email_confirmation(new_email, user)
    response: Response = await async_client.patch(
        f"/api/v1/user/change-email/confirmation?token={token}",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
