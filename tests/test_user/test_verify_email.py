import uuid

from httpx import AsyncClient

from src.user.services.email_services import _create_token_for_email_confirmation
from fastapi import status


async def test_verify_email_with_correct_token(
        async_client: AsyncClient,
        create_user_in_database,
        get_user_from_database
):
    user_in_database = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": False,
        "is_admin": False,
    }
    create_user_in_database(**user_in_database)
    token = _create_token_for_email_confirmation(user_in_database["email"], None)

    response = await async_client.get(f"/api/v1/user/verification?token={token}")
    assert response.status_code == status.HTTP_200_OK
    user_data = get_user_from_database(user_in_database["email"])
    assert user_data["is_active"] is True


async def test_verify_email_with_incorrect_token(
        async_client: AsyncClient,
        create_user_in_database,
        get_user_from_database
):
    user_in_database = {
        "user_id": str(uuid.uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": False,
        "is_admin": False,
    }
    create_user_in_database(**user_in_database)
    token = _create_token_for_email_confirmation(user_in_database["email"], None) + \
        "something"

    response = await async_client.get(f"/api/v1/user/verification?token={token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user_data = get_user_from_database(user_in_database["email"])
    assert user_data["is_active"] is False


