from datetime import datetime
from functools import wraps
from importlib import reload
from typing import Callable
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from src.user.services.hashing import Hasher
from src.worker import celery
from src.worker.logging import CeleryLogger
from src.worker.services.dal import CeleryDAL
from tests.conftest import TEST_SYNC_DATABASE_URL


def _db_session_manager_for_tests(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> None:
        engine = create_engine(url=TEST_SYNC_DATABASE_URL, echo=True)
        session = sessionmaker(engine)
        db_session: Session = session()
        celery_dal: CeleryDAL = CeleryDAL(db_session=db_session)

        try:
            result: Callable = func(celery_dal, *args, **kwargs)
            return result
        finally:
            db_session.close()

    return wrapper


patch("src.worker.database.db_session_manager", _db_session_manager_for_tests).start()

reload(celery)


def test_send_notification_email_successfully(
    celery_app: Celery,
    celery_worker: None,
    create_event_in_database: Callable,
    create_task_in_database: Callable,
    create_user_in_database: Callable,
    create_pet_in_database: Callable,
    get_sync_session: Session,
    get_event_from_database: Callable,
    get_task_from_database: Callable,
):
    with patch("src.worker.celery.send_email") as mock_send_email:
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

        event_data: dict = {
            "event_id": str(uuid4()),
            "title": "some title",
            "content": "some content",
            "scheduled_at": datetime(
                year=datetime.now().year + 1,
                month=10,
                day=10,
                hour=10,
                minute=10,
            ),
            "pet_id": pet_data["pet_id"],
            "is_happened": False,
        }
        create_event_in_database(**event_data)

        task_data: dict = {"task_id": str(uuid4()), "event_id": event_data["event_id"]}
        create_task_in_database(**task_data)

        body: dict = {
            "title": event_data["title"],
            "content": event_data["content"],
            "pet": pet_data["name"],
            "year": event_data["scheduled_at"].year,
            "month": event_data["scheduled_at"].month,
            "day": event_data["scheduled_at"].day,
            "hour": event_data["scheduled_at"].hour,
            "minute": event_data["scheduled_at"].minute,
        }

        celery.send_notification_email(
            email=user_data["email"],
            body=body,
            event_id=event_data["event_id"],
            task_id=task_data["task_id"],
        )

        mock_send_email.assert_called_once_with(
            subject="Уведомление о событии (PetTracker)",
            data=body,
            to_email=user_data["email"],
        )

        event_from_database: dict = get_event_from_database(event_data["title"])
        assert event_from_database["is_happened"] is True

        task_record_from_database: None = get_task_from_database(event_data["event_id"])
        assert task_record_from_database is None


async def test_send_notification_email_task_not_found():
    with patch.object(CeleryLogger, "log_not_found_message") as mock_log_not_found:
        task_id: UUID = uuid4()

        celery.send_notification_email(
            email="some_email@email.ru", body={}, event_id=uuid4(), task_id=task_id
        )

        mock_log_not_found.assert_called_once_with(
            message=f"Task with id {task_id} not found"
        )


async def test_send_notification_email_event_not_found(
    create_event_in_database: Callable,
    create_pet_in_database: Callable,
    create_user_in_database: Callable,
    create_task_in_database: Callable,
):
    with patch.object(CeleryLogger, "log_not_found_message") as mock_log_not_found:
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

        event_data: dict = {
            "event_id": str(uuid4()),
            "title": "some title",
            "content": "some content",
            "scheduled_at": datetime(
                year=datetime.now().year + 1,
                month=10,
                day=10,
                hour=10,
                minute=10,
            ),
            "pet_id": pet_data["pet_id"],
            "is_happened": False,
        }
        create_event_in_database(**event_data)

        task_data: dict = {"event_id": event_data["event_id"], "task_id": str(uuid4())}
        create_task_in_database(**task_data)

        incorrect_event_id: UUID = uuid4()
        celery.send_notification_email(
            email="some_email@email.ru",
            body={},
            event_id=incorrect_event_id,
            task_id=task_data["task_id"],
        )

        mock_log_not_found.assert_called_once_with(
            message=f"Event with id {incorrect_event_id} not found"
        )


def test_send_notification_email_raised_exception(
    create_event_in_database: Callable,
    create_pet_in_database: Callable,
    create_user_in_database: Callable,
    create_task_in_database: Callable,
):
    with patch.object(CeleryLogger, "log_error") as mock_log_error, patch(
        "src.worker.celery.send_email"
    ) as mock_send_email:
        error: Exception = Exception("Some error message")
        mock_send_email.side_effect = error

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

        event_data: dict = {
            "event_id": str(uuid4()),
            "title": "some title",
            "content": "some content",
            "scheduled_at": datetime(
                year=datetime.now().year + 1,
                month=10,
                day=10,
                hour=10,
                minute=10,
            ),
            "pet_id": pet_data["pet_id"],
            "is_happened": False,
        }
        create_event_in_database(**event_data)

        task_data: dict = {"task_id": str(uuid4()), "event_id": event_data["event_id"]}
        create_task_in_database(**task_data)

        body: dict = {
            "title": event_data["title"],
            "content": event_data["content"],
            "pet": pet_data["name"],
            "year": event_data["scheduled_at"].year,
            "month": event_data["scheduled_at"].month,
            "day": event_data["scheduled_at"].day,
            "hour": event_data["scheduled_at"].hour,
            "minute": event_data["scheduled_at"].minute,
        }

        celery.send_notification_email(
            email=user_data["email"],
            body=body,
            event_id=event_data["event_id"],
            task_id=task_data["task_id"],
        )

        mock_log_error.assert_called_once_with(error)
