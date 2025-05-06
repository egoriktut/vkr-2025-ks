import os
import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BROKER_URL"] = "memory://"
os.environ["MODEL_URL"] = "http://mock-model"

from auth.schemas import (
    ConfirmRegistrationSchema,
    RegistrationSchema,
    ResetPasswordSchema,
    ResetPasswordSchemaCode,
)

# Импортируем тестируемые модули
from auth.services import AuthService
from auth.utils import (
    generate_token,
    generate_verification_code,
    get_password_hash,
    send_verification_email,
    verify_password,
)
from db.models import User


# Фикстуры для тестовых данных
@pytest.fixture
def registration_data():
    return RegistrationSchema(email="test@example.com", password="securepassword123")


@pytest.fixture
def confirm_registration_data():
    return ConfirmRegistrationSchema(email="test@example.com", verification_code="ABCD")


@pytest.fixture
def reset_password_data():
    return ResetPasswordSchema(
        email="test@example.com", verification_code="ABCD", password="newpassword123"
    )


@pytest.fixture
def reset_password_code_data():
    return ResetPasswordSchemaCode(email="test@example.com")


@pytest.fixture
def mock_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password=get_password_hash("securepassword123"),
        verification_code="ABCD",
        activated=False,
        token=None,
    )


@pytest.fixture
def activated_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password=get_password_hash("securepassword123"),
        verification_code="",
        activated=True,
        token=str(uuid4()),
    )


# Тесты для AuthService
class TestAuthService:
    """Тесты для сервиса аутентификации"""

    @patch("auth.services.send_verification_email")
    def test_register_user_success(self, mock_send_email, registration_data, mock_user):
        """Тест успешной регистрации пользователя"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        new_user = mock_user
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = new_user

        result = AuthService.register_user(db, registration_data)

        assert result.email == registration_data.email
        assert result.hashed_password != registration_data.password
        assert len(result.verification_code) == 4
        mock_send_email.assert_called()

    def test_register_user_email_exists(self, registration_data, mock_user):
        """Тест регистрации с существующим email"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            AuthService.register_user(db, registration_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email уже используется" in str(exc_info.value.detail)

    def test_register_user_short_password(self, registration_data):
        """Тест регистрации с коротким паролем"""
        db = MagicMock(spec=Session)
        registration_data.password = "123"
        registration_data.email = "test2@example.com"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.register_user(db, registration_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        print(str(exc_info.value.detail))
        assert "Слишком короткий пароль" in str(exc_info.value.detail)

    def test_login_user_success(self, registration_data, activated_user):
        """Тест успешного входа"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = activated_user

        token = AuthService.login_user(db, registration_data)

        assert token == activated_user.token

    def test_login_user_not_found(self, registration_data):
        """Тест входа несуществующего пользователя"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            AuthService.login_user(db, registration_data)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Пользователь не найден" in str(exc_info.value.detail)

    def test_login_user_not_activated(self, registration_data, mock_user):
        """Тест входа неактивированного пользователя"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            AuthService.login_user(db, registration_data)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Пользователь не активирован" in str(exc_info.value.detail)

    def test_login_user_wrong_password(self, registration_data, activated_user):
        """Тест входа с неверным паролем"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = activated_user
        registration_data.password = "wrongpassword"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.login_user(db, registration_data)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Неверный пароль" in str(exc_info.value.detail)

    @patch("auth.services.send_verification_email")
    def test_resend_verification_code_success(
        self, mock_send_email, registration_data, mock_user
    ):
        """Тест повторной отправки кода подтверждения"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        AuthService.resend_verification_code(db, registration_data)

        assert mock_user.verification_code != "ABCD"  # Код должен измениться
        mock_send_email.assert_called_once()
        db.commit.assert_called_once()

    def test_confirm_registration_success(self, confirm_registration_data, mock_user):
        """Тест успешного подтверждения регистрации"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AuthService.confirm_registration(db, confirm_registration_data)

        assert result.activated is True
        assert result.verification_code == ""
        db.commit.assert_called_once()

    def test_confirm_registration_wrong_code(
        self, confirm_registration_data, mock_user
    ):
        """Тест подтверждения с неверным кодом"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = mock_user
        confirm_registration_data.verification_code = "WRONG"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.confirm_registration(db, confirm_registration_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Неверный код подтверждения" in str(exc_info.value.detail)

    @patch("auth.services.send_verification_email")
    def test_send_code_verification_email_success(
        self, mock_send_email, reset_password_code_data, activated_user
    ):
        """Тест отправки кода для сброса пароля"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = activated_user

        AuthService.send_code_verification_email(db, reset_password_code_data.email)

        mock_send_email.assert_called_once()
        db.commit.assert_called_once()

    def test_reset_password_success(self, reset_password_data, activated_user):
        """Тест успешного сброса пароля"""
        db = MagicMock(spec=Session)
        activated_user.verification_code = "ABCD"
        db.query.return_value.filter.return_value.first.return_value = activated_user

        result = AuthService.reset_password(db, reset_password_data)

        assert verify_password(reset_password_data.password, result.hashed_password)
        assert result.verification_code == ""
        db.commit.assert_called_once()


# Тесты для утилит
class TestAuthUtils:
    """Тесты для вспомогательных функций аутентификации"""

    def test_generate_token(self):
        """Тест генерации токена"""
        token = generate_token()
        assert isinstance(token, str)
        assert len(token) == 36  # Длина UUID4

    def test_generate_verification_code(self):
        """Тест генерации кода подтверждения"""
        code = generate_verification_code()
        assert isinstance(code, str)
        assert len(code) == 4

    def test_verify_password(self):
        """Тест проверки пароля"""
        password = "testpassword"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    @patch("smtplib.SMTP_SSL")
    def test_send_verification_email(self, mock_smtp):
        """Тест отправки email с кодом подтверждения"""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        send_verification_email("test@example.com", "ABCD")

        mock_smtp.assert_called_once_with("smtp.mail.ru", 465)
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.close.assert_called_once()


# Тесты для схем
class TestAuthSchemas:
    """Тесты для Pydantic схем"""

    def test_confirm_registration_schema(self, confirm_registration_data):
        """Тест схемы подтверждения регистрации"""
        assert confirm_registration_data.email == "test@example.com"
        assert confirm_registration_data.verification_code == "ABCD"

    def test_reset_password_schema(self, reset_password_data):
        """Тест схемы сброса пароля"""
        assert reset_password_data.email == "test@example.com"
        assert reset_password_data.verification_code == "ABCD"
        assert reset_password_data.password == "newpassword123"

    def test_reset_password_code_schema(self, reset_password_code_data):
        """Тест схемы запроса кода сброса"""
        assert reset_password_code_data.email == "test@example.com"
