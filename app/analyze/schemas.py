from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class FileSchema(BaseModel):
    decrypt: Optional[str]
    decrypt_plain: Optional[str]
    pandas_tables: Optional[str]


class KSAttributes(BaseModel):
    files: List[dict]
    files_parsed: List[str]
    auction_id: int
    name: str
    isContractGuaranteeRequired: float | bool
    isLicenseProduction: str | bool
    deliveries: List[dict]
    startCost: float
    contractCost: float | None


class ValidationOption(int, Enum):
    VALIDATE_NAMING = 1
    VALIDATE_PERFORM_CONTRACT_REQUIRED = 2
    VALIDATE_LICENSE = 3
    VALIDATE_DELIVERY_GRAPHIC = 4
    VALIDATE_PRICE = 5
    VALIDATE_SPECIFICATIONS = 6

    def description(self) -> str:
        descriptions = {
            1: "Наименование закупки совпадает с наименованием в техническом задании и/или в проекте контракта",
            2: "Обеспечение исполнения контракта - требуется",
            3: "Наличие сертификатов/лицензий",
            4: "График поставки И этап поставки",
            5: "Максимальное значение цены контракта ИЛИ начальная цена",
            6: "Спецификации",
        }
        return descriptions.get(self.value, "Unknown validation")


class AnalyzeUrlRequest(BaseModel):
    urls: List[str]
    validate_params: List[ValidationOption]


class AnalyzeUrlResponse(BaseModel):
    task_ids: Dict[str, str]
    status: str


class ValidationOptionResult(BaseModel):
    status: bool
    description: str


class Result(BaseModel):
    url: str
    analysis: Dict[ValidationOption, ValidationOptionResult]


class AnalysisResultResponse(BaseModel):
    status: str
    result: Optional[Result]


class TwoTextsInput(BaseModel):
    """Схема запроса для двух текстовых строк для вычисления сходства."""

    first: str
    second: str
