from typing import Callable
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_update_pet_successfully(
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

    parameters_for_update: dict = {
        "name": "New name",
        "species": "Dog",
        "breed": "New breed",
        "weight": 25,
        "gender": "female",
    }

    response: Response = await async_client.patch(
        f"/api/v1/pet/?pet_id={pet_data['pet_id']}",
        json=parameters_for_update,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["name"] == parameters_for_update["name"]
    assert response_data["species"] == parameters_for_update["species"]
    assert response_data["breed"] == parameters_for_update["breed"]
    assert response_data["weight"] == parameters_for_update["weight"]
    assert response_data["gender"] == parameters_for_update["gender"]

    updated_pet: dict = get_pet_from_database(parameters_for_update["name"])
    assert updated_pet["name"] == parameters_for_update["name"]
    assert updated_pet["species"] == parameters_for_update["species"]
    assert updated_pet["breed"] == parameters_for_update["breed"]
    assert updated_pet["weight"] == parameters_for_update["weight"]
    assert updated_pet["gender"] == parameters_for_update["gender"]

    pet_with_old_data: dict = get_pet_from_database(pet_data["name"])
    assert pet_with_old_data == {}


async def test_update_pet_successfully_not_all_params(
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

    parameters_for_update: dict = {
        "name": "New name",
        "species": "Dog",
        "breed": "New breed",
    }

    response: Response = await async_client.patch(
        f"/api/v1/pet/?pet_id={pet_data['pet_id']}",
        json=parameters_for_update,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["name"] == parameters_for_update["name"]
    assert response_data["species"] == parameters_for_update["species"]
    assert response_data["breed"] == parameters_for_update["breed"]
    assert response_data["weight"] == pet_data["weight"]
    assert response_data["gender"] == pet_data["gender"]

    updated_pet: dict = get_pet_from_database(parameters_for_update["name"])
    assert updated_pet["name"] == parameters_for_update["name"]
    assert updated_pet["species"] == parameters_for_update["species"]
    assert updated_pet["breed"] == parameters_for_update["breed"]
    assert updated_pet["weight"] == pet_data["weight"]
    assert updated_pet["gender"] == pet_data["gender"]

    pet_with_old_data: dict = get_pet_from_database(pet_data["name"])
    assert pet_with_old_data == {}


async def test_update_pet_incorrect_uuid(
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

    response: Response = await async_client.patch(
        "/api/v1/pet/?pet_id=incorrect_id",
        json={},
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


async def test_update_pet_no_auth(async_client: AsyncClient):
    response = await async_client.patch(
        f"/api/v1/pet/?pet_id={uuid4()}",
        json={},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_update_pet_inactive_user(
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

    response: Response = await async_client.patch(
        "/api/v1/pet/",
        json={},
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


async def test_update_pet_not_found(
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

    parameters_for_update: dict = {
        "name": "New name",
        "species": "Dog",
        "breed": "New breed",
    }

    response: Response = await async_client.patch(
        f"/api/v1/pet/?pet_id={uuid4()}",
        json=parameters_for_update,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Pet with this id not found"}


async def test_update_pet_another_users_pet(
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

    parameters_for_update: dict = {"breed": "New breed"}

    response: Response = await async_client.patch(
        f"/api/v1/pet/?pet_id={pet_data['pet_id']}",
        json=parameters_for_update,
        headers=create_test_auth_headers_for_user(another_user_data["email"]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Pet with this id not found"}


@pytest.mark.parametrize(
    "params_for_update, expected_detail",
    [
        (
            None,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body"],
                        "msg": "Field required",
                        "input": None,
                    }
                ]
            },
        ),
        ({}, {"detail": "At least one parameter must be provided"}),
        (
            {
                "name": "some name",
                "species": "45",
                "breed": "Some breed",
                "weight": 15,
                "gender": "male",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "species"],
                        "msg": "Value error, Species contains incorrect symbols",
                        "input": "45",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "name": "some name",
                "species": "Cat",
                "breed": "Some breed",
                "weight": "some weight",
                "gender": "male",
            },
            {
                "detail": [
                    {
                        "type": "float_parsing",
                        "loc": ["body", "weight"],
                        "msg": "Input should be a valid number, unable to parse string as a number",
                        "input": "some weight",
                    }
                ]
            },
        ),
        (
            {
                "name": "some name",
                "species": "Cat",
                "breed": "Some breed",
                "weight": -43,
                "gender": "male",
            },
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "weight"],
                        "msg": "Value error, Weight can only be a positive number",
                        "input": -43,
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {
                "name": "some name",
                "species": "Cat",
                "breed": "Some breed",
                "weight": "some weight",
                "gender": "ok",
            },
            {
                "detail": [
                    {
                        "type": "enum",
                        "loc": ["body", "gender"],
                        "msg": "Input should be 'male' or 'female'",
                        "input": "ok",
                        "ctx": {"expected": "'male' or 'female'"},
                    },
                    {
                        "type": "float_parsing",
                        "loc": ["body", "weight"],
                        "msg": "Input should be a valid number, unable to parse string as a number",
                        "input": "some weight",
                    },
                ]
            },
        ),
    ],
)
async def test_update_pet_negative(
    params_for_update: dict,
    expected_detail: dict,
    create_user_in_database: Callable,
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

    response: Response = await async_client.patch(
        f"/api/v1/pet/?pet_id={uuid4()}",
        json=params_for_update,
        headers=create_test_auth_headers_for_user(email=user_data["email"]),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_detail
