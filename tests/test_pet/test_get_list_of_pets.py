from typing import Callable
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_get_list_of_pets_user_without_pets(
    create_user_in_database, async_client: AsyncClient
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.get(
        "/api/v1/pet/list-of-pets",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "This user does not have pets"}


async def test_get_list_of_pets_user_has_one_pet(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    async_client: AsyncClient,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**pet_data)

    response: Response = await async_client.get(
        "/api/v1/pet/list-of-pets",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"pet_id": pet_data["pet_id"], "name": pet_data["name"]}]


async def test_get_list_of_pets_user_has_several_pets(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    async_client: AsyncClient,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    first_pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**first_pet_data)

    second_pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Another name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": user_data["user_id"],
        "gender": "female",
    }
    create_pet_in_database(**second_pet_data)

    response: Response = await async_client.get(
        "/api/v1/pet/list-of-pets",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"pet_id": first_pet_data["pet_id"], "name": first_pet_data["name"]},
        {"pet_id": second_pet_data["pet_id"], "name": second_pet_data["name"]},
    ]


async def test_get_list_of_pets_other_pets_exist(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    async_client: AsyncClient,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    another_user_data: dict = {
        "user_id": str(uuid4()),
        "username": "another_username",
        "email": "another_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**another_user_data)

    first_pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**first_pet_data)

    another_pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": another_user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**another_pet_data)

    response: Response = await async_client.get(
        "/api/v1/pet/list-of-pets",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"pet_id": first_pet_data["pet_id"], "name": first_pet_data["name"]},
    ]


async def test_get_list_of_pets_no_auth(async_client: AsyncClient):
    response: Response = await async_client.get(
        "/api/v1/pet/list-of-pets",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_get_list_of_pets_inactive_user(
    create_user_in_database: Callable, async_client: AsyncClient
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": False,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.get(
        "/api/v1/pet/list-of-pets",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}
