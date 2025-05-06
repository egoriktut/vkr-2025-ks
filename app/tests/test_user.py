import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BROKER_URL"] = "memory://"
os.environ["MODEL_URL"] = "http://mock-model"

from db.models import User
from user.schemas import UserBase, UserChangeCredentials
from user.services import UserService


# Фикстуры для тестовых данных
@pytest.fixture
def mock_user():
    return User(
        id=1,
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        created_at=datetime.now(),
        token="test_token",
    )


@pytest.fixture
def user_change_credentials():
    return UserChangeCredentials(first_name="NewFirstName", last_name="NewLastName")


@pytest.fixture
def mock_db_session(mock_user):
    db = MagicMock(spec=Session)
    db.query.return_value.filter_by.return_value.first.return_value = mock_user
    return db


# Тесты для UserService
class TestUserService:
    """Тесты для сервиса пользователя"""

    def test_get_user_by_token_success(self, mock_db_session, mock_user):
        """Тест успешного получения пользователя по токену"""
        result = UserService.get_user_by_token(mock_db_session, "test_token")

        assert isinstance(result, UserBase)
        assert result.email == mock_user.email
        assert result.first_name == mock_user.first_name
        assert result.last_name == mock_user.last_name
        assert result.created_at == mock_user.created_at

        mock_db_session.query.assert_called_once_with(User)
        mock_db_session.query.return_value.filter_by.assert_called_once_with(
            token="test_token"
        )

    def test_get_user_by_token_not_found(self, mock_db_session):
        """Тест попытки получения несуществующего пользователя"""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        with pytest.raises(HTTPException) as exc_info:
            UserService.get_user_by_token(mock_db_session, "invalid_token")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

    def test_change_credentials_success(
        self, mock_db_session, mock_user, user_change_credentials
    ):
        """Тест успешного изменения данных пользователя"""
        result = UserService.change_credentials(
            mock_db_session, "test_token", user_change_credentials
        )

        assert isinstance(result, UserBase)
        assert result.first_name == "NewFirstName"
        assert result.last_name == "NewLastName"

        # Проверяем, что данные сохранились в БД
        assert mock_user.first_name == "NewFirstName"
        assert mock_user.last_name == "NewLastName"

        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_user)

    def test_change_credentials_partial_update(self, mock_db_session, mock_user):
        """Тест частичного обновления данных пользователя"""
        partial_data = UserChangeCredentials(
            first_name="OnlyFirstName", last_name="OnlyLastName"
        )

        result = UserService.change_credentials(
            mock_db_session, "test_token", partial_data
        )

        assert result.first_name == "OnlyFirstName"
        assert result.last_name == "OnlyLastName"  # Осталось прежним

    def test_change_credentials_user_not_found(
        self, mock_db_session, user_change_credentials
    ):
        """Тест изменения данных несуществующего пользователя"""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        with pytest.raises(HTTPException) as exc_info:
            UserService.change_credentials(
                mock_db_session, "invalid_token", user_change_credentials
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)


class TestUserSchemas:
    """Тесты для Pydantic схем пользователя"""

    def test_user_base_schema(self, mock_user):
        """Тест схемы базовых данных пользователя"""
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": datetime.now().isoformat(),
        }

        user_schema = UserBase(**user_data)

        assert user_schema.email == "test@example.com"
        assert user_schema.first_name == "John"
        assert user_schema.last_name == "Doe"
        assert isinstance(user_schema.created_at, datetime)

    def test_user_change_credentials_schema(self):
        """Тест схемы изменения данных пользователя"""
        # Полное обновление
        full_update = UserChangeCredentials(
            first_name="NewFirstName", last_name="NewLastName"
        )
        assert full_update.first_name == "NewFirstName"
        assert full_update.last_name == "NewLastName"

        # Частичное обновление
        partial_update = UserChangeCredentials(first_name="OnlyFirstName")
        assert partial_update.first_name == "OnlyFirstName"
        assert partial_update.last_name is None

        # Пустое обновление (должно быть валидным)
        empty_update = UserChangeCredentials()
        assert empty_update.first_name is None
        assert empty_update.last_name is None
