from typing import Callable
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import Response

from src.user.services.hashing import Hasher
from tests.conftest import create_test_auth_headers_for_user


async def test_add_pet_successfully(
    async_client: AsyncClient,
    get_user_from_database: Callable,
    create_user_in_database: Callable,
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
        "name": "Some name",
        "species": "Cat",
        "breed": "Some breed",
        "weight": 15,
        "gender": "male",
    }
    response: Response = await async_client.post(
        "/api/v1/pet/",
        json=pet_data,
        headers=create_test_auth_headers_for_user(email=user_data["email"]),
    )

    assert response.status_code == status.HTTP_200_OK

    response_data: dict = response.json()
    assert response_data["name"] == pet_data["name"]
    assert response_data["species"] == pet_data["species"]
    assert response_data["weight"] == pet_data["weight"]
    assert response_data["gender"] == pet_data["gender"]
    assert response_data["events"] == []

    created_pet_data: dict = get_pet_from_database(pet_data["name"])
    assert created_pet_data["species"] == pet_data["species"]
    assert created_pet_data["breed"] == pet_data["breed"]
    assert created_pet_data["weight"] == pet_data["weight"]
    assert created_pet_data["gender"] == pet_data["gender"]
    assert created_pet_data["owner_id"] == user_data["user_id"]


@pytest.mark.parametrize(
    "request_data",
    [
        {"name": "Some name", "species": "Cat", "weight": 15, "gender": "male"},
        {
            "name": "Some name",
            "species": "Cat",
            "breed": "Some breed",
            "gender": "male",
        },
    ],
)
async def test_add_pet_incomplete_data(
    request_data: dict,
    get_pet_from_database: Callable,
    async_client: AsyncClient,
    create_user_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.post(
        "/api/v1/pet/",
        json=request_data,
        headers=create_test_auth_headers_for_user(email=user_data["email"]),
    )

    assert response.status_code == status.HTTP_200_OK

    response_data: dict = response.json()
    assert response_data["name"] == request_data["name"]
    assert response_data["species"] == request_data["species"]
    assert response_data["breed"] == request_data.get("breed", None)
    assert response_data["weight"] == request_data.get("weight", None)
    assert response_data["gender"] == request_data["gender"]
    assert response_data["events"] == []

    created_pet_data: dict = get_pet_from_database(request_data["name"])
    assert created_pet_data["species"] == request_data["species"]
    assert created_pet_data["breed"] == request_data.get("breed", None)
    assert created_pet_data["weight"] == request_data.get("weight", None)
    assert created_pet_data["owner_id"] == user_data["user_id"]
    assert created_pet_data["gender"] == request_data["gender"]


@pytest.mark.parametrize(
    "pet_data_for_creation, expected_detail",
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
        (
            {},
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "name"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "species"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "gender"],
                        "msg": "Field required",
                        "input": {},
                    },
                ]
            },
        ),
        (
            {"species": "Cat", "breed": "Some breed", "weight": 15, "gender": "male"},
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "name"],
                        "msg": "Field required",
                        "input": {
                            "species": "Cat",
                            "breed": "Some breed",
                            "weight": 15,
                            "gender": "male",
                        },
                    }
                ]
            },
        ),
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
async def test_add_pet_negative(
    pet_data_for_creation: dict,
    expected_detail: dict,
    async_client: AsyncClient,
    create_user_in_database: Callable,
):
    user_data: dict = {
        "user_id": str(uuid4()),
        "username": "some_username",
        "email": "some_email@email.ru",
        "hashed_password": Hasher().get_password_hash("1234"),
        "is_active": True,
    }
    create_user_in_database(**user_data)

    response: Response = await async_client.post(
        "/api/v1/pet/",
        json=pet_data_for_creation,
        headers=create_test_auth_headers_for_user(email=user_data["email"]),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expected_detail


async def test_add_pet_no_auth(async_client: AsyncClient):
    response: Response = await async_client.get(
        "/api/v1/pet/",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_add_pet_inactive_user(
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
        "/api/v1/pet/", headers=create_test_auth_headers_for_user(user_data["email"])
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}
