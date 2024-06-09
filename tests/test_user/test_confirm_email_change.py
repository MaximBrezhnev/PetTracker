import uuid

import pytest
from httpx import AsyncClient
from fastapi import status

from src.user.models import User
from src.user.services.auth_services import get_password_hash
from src.user.services.email_services import _create_token_for_email_confirmation


async def test_confirm_email_change_successfully(
        async_client: AsyncClient,
        get_user_from_database,
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
    new_email = "new_email@mail.ru"
    user = User(**user_data)

    token = _create_token_for_email_confirmation(new_email, user)
    response = await async_client.get(
        f"/api/v1/user/change-email/confirmation?token={token}",
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert response_data["email"] == new_email
    assert response_data["username"] == user_data["username"]

    user_with_new_email = get_user_from_database(new_email)
    assert user_with_new_email is not None
    user_with_old_email = get_user_from_database(user_data["email"])
    assert user_with_old_email is None


async def test_confirm_email_change_duplicate(
        async_client: AsyncClient,
        get_user_from_database,
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
    new_email = "new_email@email.ru"
    user = User(**user_data)

    another_user_data = {
        "user_id": str(uuid.uuid4()),
        "username": "another_username",
        "email": "new_email@email.ru",
        "hashed_password": get_password_hash("1234"),
        "is_active": True,
        "is_admin": False,
    }
    create_user_in_database(**another_user_data)

    token = _create_token_for_email_confirmation(new_email, user)
    response = await async_client.get(
        f"/api/v1/user/change-email/confirmation?token={token}",
    )

    assert response.status_code == status.HTTP_409_CONFLICT

    user = get_user_from_database(user_data["email"])
    assert user["email"] == user_data["email"]


async def test_confirm_email_change_incorrect_token(
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
    new_email = "new_email@email.ru"
    user = User(**user_data)

    token = _create_token_for_email_confirmation(new_email, user)
    response = await async_client.get(
        f"/api/v1/user/change-email/confirmation?token={token}+123",
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_confirm_email_change_user_is_inactive(
        create_user_in_database,
        async_client: AsyncClient
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
    new_email = "new_email@email.ru"
    user = User(**user_data)

    token = _create_token_for_email_confirmation(new_email, user)
    response = await async_client.get(
        f"/api/v1/user/change-email/confirmation?token={token}",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


