from typing import Callable
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_delete_pet_successfully(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    async_client: AsyncClient,
    get_pet_from_database: Callable,
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

    response: Response = await async_client.delete(
        f"/api/v1/pet/?pet_id={pet_data['pet_id']}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Pet was deleted successfully"}

    pet_after_deleting: dict = get_pet_from_database(pet_data["name"])
    assert pet_after_deleting == {}


async def test_delete_pet_incorrect_uuid(
    create_user_in_database: Callable, async_client: AsyncClient
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.delete(
        "/api/v1/pet/?pet_id=incorrect_id",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "pet_id"],
                "msg": "Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` "
                "followed by [0-9a-fA-F-], found `i` at 1",
                "input": "incorrect_id",
                "ctx": {
                    "error": "invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], "
                    "found `i` at 1"
                },
            }
        ]
    }


async def test_delete_pet_no_auth(async_client: AsyncClient):
    response: Response = await async_client.delete(
        f"/api/v1/pet/?pet_id={uuid4()}",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_delete_pet_inactive_user(
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

    response: Response = await async_client.delete(
        f"/api/v1/pet/?pet_id={uuid4()}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


async def test_delete_pet_does_not_exist(
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    async_client: AsyncClient,
    get_pet_from_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.delete(
        f"/api/v1/pet/?pet_id={uuid4()}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Pet with this id belonging to the current user not found"
    }


async def test_delete_pet_another_users_pet(
    create_user_in_database: Callable,
    async_client: AsyncClient,
    create_pet_in_database: Callable,
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

    pet_data: dict = {
        "pet_id": str(uuid4()),
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "owner_id": another_user_data["user_id"],
        "gender": "male",
    }
    create_pet_in_database(**pet_data)

    response: Response = await async_client.delete(
        f"/api/v1/pet/?pet_id={pet_data['pet_id']}",
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Pet with this id belonging to the current user not found"
    }
