from typing import Dict, List

from analyze.schemas import Result, ValidationOption
from analyze.scraper import ParserWeb
from analyze.validation import KSValidator
from celery import Celery
from config import settings

celery_app = Celery("app", broker=settings.BROKER_URL, backend=settings.BACKEND_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

ks_validator = KSValidator(settings.MODEL_URL)


@celery_app.task
def start_analysis_task(url: str, validate_params: List[ValidationOption]) -> Dict:
    page_data = ParserWeb(url).fetch_and_parse()
    if page_data is None:
        raise Exception()
    analysis_result = ks_validator.validate_content(page_data, validate_params)

    return Result(url=url, analysis=analysis_result).dict()
