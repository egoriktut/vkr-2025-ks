from pydantic import BaseModel


class TwoTextsInput(BaseModel):
    """Схема запроса для двух текстовых строк для вычисления сходства."""

    first: str
    second: str
