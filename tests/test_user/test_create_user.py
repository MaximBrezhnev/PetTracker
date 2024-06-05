import uuid

import pytest
from httpx import AsyncClient
from fastapi import status


async def test_create_user_user_does_not_exist(
        async_client: AsyncClient,
        get_user_from_database,
):
    user_data = {
        "username": "some username",
        "email": "some_emailftgnbxtdgfbcf@email.ru",
        "password1": "1234",
        "password2": "1234",
    }

    # Здесь мок для почты

    response = await async_client.post(
        "/api/v1/user/", json=user_data
    )

    assert response.status_code == status.HTTP_200_OK
    created_user_data = get_user_from_database(user_data["email"])
    assert created_user_data["username"] == user_data["username"]
    assert created_user_data["email"] == user_data["email"]
    assert created_user_data["is_active"] is False
    assert created_user_data["is_admin"] is False

    # Здесь проверка, что функция вызывалась


@pytest.mark.parametrize(
    "username, new_username, result_username",
    [
        ("some_username", "some_username", "some_username"),
        ("some_username", "new_username", "new_username"),
    ]
)
async def test_create_user_inactive_user_exists(
        async_client: AsyncClient,
        get_user_from_database,
        create_user_in_database,
        username,
        new_username,
        result_username
):
    inactive_user_data = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "email": "some_email@email.ru",
        "hashed_password": "1234",
        "is_active": False,
        "is_admin": False,
       }
    new_user_data = {
           "username": new_username,
           "email": "some_email@email.ru",
           "password1": "1234",
           "password2": "1234",
       }
    # Здесь мок для почты
    create_user_in_database(**inactive_user_data)
    response = await async_client.post(
        "/api/v1/user/", json=new_user_data
    )

    assert response.status_code == status.HTTP_200_OK

    created_user_data = get_user_from_database(new_user_data["email"])
    assert str(created_user_data["user_id"]) == inactive_user_data["user_id"]
    assert created_user_data["username"] == result_username
    assert created_user_data["email"] == inactive_user_data["email"]
    assert created_user_data["is_active"] is False
    assert created_user_data["is_admin"] is False

    # Здесь проверка вызова почты


async def test_create_user_active_user_exists():
    pass


async def test_create_user_cannot_send_email():
    pass


async def test_create_user_username_duplicate():
    pass


async def test_create_user_negative():
    pass



