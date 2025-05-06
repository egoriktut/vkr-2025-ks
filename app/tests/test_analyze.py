# test_analyze.py
import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BROKER_URL"] = "memory://"
os.environ["MODEL_URL"] = "http://mock-model"

from analyze.api import router as analyze_router
from analyze.api_utils import (
    clear_task_history_user,
    create_new_tasks,
    get_tasks_by_user_token,
    process_data,
    process_task,
    send_task_email,
)
from analyze.schemas import (
    AnalyzeUrlRequest,
    AnalyzeUrlResponse,
    KSAttributes,
    TwoTextsInput,
    ValidationOption,
    ValidationOptionResult,
)
from analyze.scraper import FilesProcessor, ParserWeb
from analyze.utils import (
    clear_text,
    convert_to_pdf,
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_xlsx,
    read_file,
)

# Импортируем тестируемые модули
from analyze.validation import KSValidator, ModelRequest
from celery.result import AsyncResult
from db.models import TaskHistory, User


# Фикстуры для тестовых данных
@pytest.fixture
def mock_page_data():
    return KSAttributes(
        auction_id=123,
        name="Test Purchase",
        files=[{"name": "test.pdf", "downloads_link": "http://example.com/test.pdf"}],
        files_parsed=["Test document content"],
        isContractGuaranteeRequired=True,
        isLicenseProduction=False,
        deliveries=[
            {
                "periodDateFrom": "01.01.2023 00:00:00",
                "periodDateTo": "31.01.2023 00:00:00",
                "periodDaysFrom": 1,
                "periodDaysTo": 31,
                "items": [
                    {
                        "name": "Item 1",
                        "sum": 100.0,
                        "quantity": 10,
                        "costPerUnit": 10.0,
                    }
                ],
            }
        ],
        startCost=1000.0,
        contractCost=950.0,
    )


@pytest.fixture
def mock_user():
    return User(id=1, email="test@example.com", token="test_token")


@pytest.fixture
def mock_db_session(mock_user):
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = mock_user
    return db


# Тесты для KSValidator
class TestKSValidator:
    """Тесты для валидатора конкурсных ситуаций"""

    @patch("analyze.validation.ModelRequest")
    def test_validate_content(self, mock_model_request, mock_page_data):
        """Тест основного метода validate_content"""
        validator = KSValidator()
        validator.model_requests = mock_model_request

        # Настраиваем моки для методов модели
        mock_model_request.llama_prompt.return_value = True
        mock_model_request.check_similarity_transformer.return_value = 0.8
        mock_model_request.check_similarity2_transformer.return_value = 3.0

        # Тестируем все варианты валидации
        results = validator.validate_content(
            mock_page_data,
            [
                ValidationOption.VALIDATE_NAMING,
                ValidationOption.VALIDATE_PERFORM_CONTRACT_REQUIRED,
                ValidationOption.VALIDATE_LICENSE,
                ValidationOption.VALIDATE_DELIVERY_GRAPHIC,
                ValidationOption.VALIDATE_PRICE,
                ValidationOption.VALIDATE_SPECIFICATIONS,
            ],
        )

        assert len(results) == 6
        assert all(isinstance(v, ValidationOptionResult) for v in results.values())

    def test_validate_naming(self, mock_page_data):
        """Тест валидации наименования"""
        validator = KSValidator("url")

        with patch.object(
            validator.model_requests, "check_similarity_transformer", return_value=0.85
        ):
            result = validator.validate_naming(mock_page_data)
            assert result.status is True

        with patch.object(
            validator.model_requests, "check_similarity_transformer", return_value=0.65
        ):
            with patch.object(
                validator.model_requests,
                "check_similarity2_transformer",
                return_value=3,
            ):
                result = validator.validate_naming(mock_page_data)
                assert result.status is True

        with patch.object(
            validator.model_requests, "check_similarity_transformer", return_value=0.65
        ):
            with patch.object(
                validator.model_requests,
                "check_similarity2_transformer",
                return_value=5,
            ):
                with patch.object(
                    validator.model_requests, "llama_prompt", return_value=True
                ):
                    result = validator.validate_naming(mock_page_data)
                    assert result.status is True

        with patch.object(
            validator.model_requests, "check_similarity_transformer", return_value=0.65
        ):
            with patch.object(
                validator.model_requests,
                "check_similarity2_transformer",
                return_value=5,
            ):
                with patch.object(
                    validator.model_requests, "llama_prompt", return_value=False
                ):
                    result = validator.validate_naming(mock_page_data)
                    assert result.status is False

    def test_validate_price(self, mock_page_data):
        """Тест валидации цены"""
        validator = KSValidator("url")

        with patch.object(validator.model_requests, "llama_prompt", return_value=False):
            result = validator.validate_price(mock_page_data)
            assert result.status is False

    def test_validate_delivery_graphic(self, mock_page_data):
        """Тест валидации графика поставки"""
        validator = KSValidator()

        # Тест с корректными датами
        result = validator.validate_delivery_graphic(mock_page_data)
        assert isinstance(result, ValidationOptionResult)

        # Тест с некорректными датами
        invalid_data = mock_page_data.copy()
        invalid_data.deliveries[0]["periodDateFrom"] = "invalid_date"
        result = validator.validate_delivery_graphic(invalid_data)
        assert result.status is False


# Тесты для ParserWeb
class TestParserWeb:
    """Тесты для парсера веб-страниц"""

    @patch("requests.get")
    def test_is_real_url(self, mock_get):
        """Тест проверки существования URL"""
        mock_get.return_value.status_code = 200
        parser = ParserWeb("http://example.com")
        assert parser.is_real_url() is True

        mock_get.return_value.status_code = 404
        assert parser.is_real_url() is False

    @patch("requests.get")
    def test_get_attributes_ks(self, mock_get):
        """Тест получения атрибутов конкурсной ситуации"""
        test_data = {
            "name": "Test Purchase",
            "files": [{"name": "test.pdf", "id": "123"}],
            "contractGuaranteeAmount": 5000.0,
            "isContractGuaranteeRequired": True,
            "isLicenseProduction": False,
            "uploadLicenseDocumentsComment": "",
            "deliveries": [{"items": []}],
            "startCost": 1000.0,
            "contractCost": 950.0,
        }
        mock_get.return_value.content = json.dumps(test_data).encode()

        parser = ParserWeb("http://example.com/123")
        result = parser.get_attributes_ks()

        assert result is not None
        assert result.name == "Test Purchase"
        assert result.auction_id == 123


# Тесты для API utils
class TestAPIUtils:
    """Тесты для вспомогательных функций API"""

    @patch("analyze.scraper.ParserWeb")
    @patch("analyze.scraper.FilesProcessor")
    def test_process_data(self, mock_files_processor, mock_parser_web, mock_page_data):
        """Тест обработки данных"""
        mock_parser = MagicMock()
        mock_parser.fetch_and_parse.return_value = mock_page_data
        mock_parser_web.return_value = mock_parser

        mock_processor = MagicMock()
        mock_processor.generate_parsed_files_data.return_value = mock_page_data
        mock_files_processor.return_value = mock_processor

        result = process_data(["http://example.com/123"])

        assert isinstance(result, dict)
        assert "http://example.com/123" in result

    @patch("sqlalchemy.orm.Session")
    def test_create_new_tasks(self, mock_session, mock_page_data, mock_user):
        """Тест создания новых задач"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        task_ids = {"http://example.com/123": "task123"}
        create_new_tasks(
            {"http://example.com/123": mock_page_data}, task_ids, db, "test_token"
        )

        db.add.assert_called()
        db.commit.assert_called_once()


# Тесты для utils
class TestUtils:
    """Тесты для вспомогательных утилит"""

    def test_clear_text(self):
        """Тест очистки текста"""
        dirty_text = "  Test \n text!@# with 123   "
        clean_text = clear_text(dirty_text)
        assert clean_text == "test text with 123"
