import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BROKER_URL"] = "memory://"
os.environ["MODEL_URL"] = "http://mock-model"

from api.api import ping, router

# Импортируем тестируемые модули
from api.utils import get_current_token, security
from sqlalchemy.orm import Session


class TestUtils:
    """Тесты для вспомогательных функций"""

    @pytest.mark.asyncio
    @patch('api.utils.security')
    async def test_get_current_token_success(self, mock_security):
        """Тест успешного получения токена из заголовков"""
        # Мокаем credentials
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "test_token"

        # Мокаем security (теперь как асинхронный mock)
        mock_security.return_value = AsyncMock(return_value=mock_credentials)

        result = await get_current_token(credentials=mock_credentials)

        assert result == "test_token"

    @pytest.mark.asyncio
    @patch('api.utils.security')
    async def test_get_current_token_missing(self, mock_security):
        """Тест отсутствия токена в заголовках"""
        # Создаем асинхронный mock, который вызывает исключение
        mock_security.return_value = AsyncMock()
        mock_security.return_value.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

        with pytest.raises(AttributeError) as exc_info:
            await get_current_token(credentials=None)

# Тесты для api.py
class TestAPI:
    """Тесты для API endpoints"""

    @patch("api.api.get_db")
    def test_ping_endpoint_db_connected(self, mock_get_db):
        """Тест эндпоинта ping при успешном подключении к БД"""
        # Мокаем сессию БД
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        # Создаем тестовый клиент
        test_router = APIRouter()
        test_router.get("/")(ping)

        client = TestClient(test_router)
        response = client.get("/")

        assert response.status_code == 200
        assert response.text == '"db successful connected"'

    def test_router_includes(self):
        """Тест подключения роутеров"""
        routers_mock = {
            "/",
            "/analyze",
            "/analyze/clear_task_history",
            "/analyze/send_task/{task_ids}",
            "/auth/confirm_code",
            "/auth/confirm_registration",
            "/auth/login",
            "/auth/register",
            "/auth/resend_code",
            "/auth/reset_password",
            "/auth/reset_password_code",
            "/user/account",
        }
        # Проверяем, что все роутеры подключены
        assert len(router.routes) >= 4

        # Проверяем префиксы
        included_routers = {route.path for route in router.routes}

        for route in routers_mock:
            assert route in included_routers


# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты с TestClient"""

    @patch("api.api.get_db")
    def test_full_app(self, mock_get_db):
        """Тест всего приложения с моками"""
        from main import app

        # Мокаем подключение к БД
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        client = TestClient(app)

        # Тестируем корневой эндпоинт
        response = client.get("/")
        assert response.status_code == 200
        assert "db successful connected" in response.text

        # Тестируем доступность основных маршрутов
        for prefix in ["/auth", "/analyze", "/user"]:
            response = client.get(prefix + "/")
            assert response.status_code in [404, 405, 403]
