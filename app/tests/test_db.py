import os
import sys
from datetime import datetime
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BROKER_URL"] = "memory://"
os.environ["MODEL_URL"] = "http://mock-model"

from db.database import Base
from db.database import SessionLocal as main_SessionLocal
from db.database import engine as main_engine
from db.db_operations import get_user
from db.dependencies import get_db
from db.models import TaskHistory, User


class TestDatabaseModule:
    """Тесты для database.py"""

    def test_engine_creation(self):
        """Проверка создания engine"""
        assert main_engine is not None
        assert str(main_engine.url).startswith("sqlite:///")

    def test_session_local(self):
        """Проверка фабрики сессий"""
        assert main_SessionLocal is not None
        session = main_SessionLocal()
        assert session is not None
        session.close()

    def test_base_model(self):
        """Проверка базовой модели"""
        assert Base is not None
        assert hasattr(Base, "metadata")


class TestDependenciesModule:
    """Тесты для dependencies.py"""

    def test_get_db_generator(self):
        """Проверка генератора сессии базы данных"""
        db_gen = get_db()
        assert isinstance(db_gen, Generator)

        db = next(db_gen)
        assert db is not None
        assert isinstance(db, Session)

        # Проверяем, что сессия закрывается
        try:
            next(db_gen)
        except StopIteration:
            pass

        # Проверяем, что сессия действительно закрыта
        with pytest.raises(Exception):
            db.execute("SELECT 1")


class TestModelsModule:
    """Тесты для models.py"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Фикстура для настройки тестовой базы данных"""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        yield
        self.session.close()

    def test_user_model(self):
        """Тестирование модели User"""
        user_data = {
            "email": "test@example.com",
            "hashed_password": "hashed123",
            "first_name": "John",
            "last_name": "Doe",
        }

        user = User(**user_data)
        self.session.add(user)
        self.session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed123"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert isinstance(user.created_at, datetime)
        assert user.activated is False

        # Проверка метода as_dict
        user_dict = user.as_dict
        assert isinstance(user_dict, dict)
        assert user_dict["email"] == "test@example.com"
        assert "hashed_password" in user_dict

    def test_task_history_model(self):
        """Тестирование модели TaskHistory"""
        # Сначала создаем пользователя для связи
        user = User(
            email="user@example.com",
            hashed_password="pass123",
            first_name="Alice",
            last_name="Smith",
        )
        self.session.add(user)
        self.session.commit()

        task_data = {
            "ids": "1,2,3",
            "user_id": user.id,
            "url": "http://example.com",
            "description": "Test task",
            "status": "pending",
        }

        task = TaskHistory(**task_data)
        self.session.add(task)
        self.session.commit()

        assert task.id is not None
        assert task.ids == "1,2,3"
        assert task.user_id == user.id
        assert task.url == "http://example.com"
        assert task.description == "Test task"
        assert task.status == "pending"
        assert isinstance(task.created_at, datetime)
        assert task.completed_at is None


class TestDbOperationsModule:
    """Тесты для db_operations.py"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Фикстура для настройки тестовой базы данных"""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Добавляем тестового пользователя
        self.user = User(
            email="test@example.com",
            hashed_password="hashed123",
            first_name="John",
            last_name="Doe",
        )
        self.session.add(self.user)
        self.session.commit()
        yield
        self.session.close()

    def test_get_user_existing(self):
        """Тестирование получения существующего пользователя"""
        user = get_user(self.session, self.user.id)
        assert user is not None
        assert user.id == self.user.id
        assert user.email == "test@example.com"

    def test_get_user_non_existing(self):
        """Тестирование получения несуществующего пользователя"""
        user = get_user(self.session, 999)
        assert user is None
