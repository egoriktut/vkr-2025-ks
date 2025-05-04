from typing import Dict

from analyze.api_utils import process_data, write_db
from analyze.schemas import (
    AnalysisResultResponse,
    AnalyzeUrlRequest,
    AnalyzeUrlResponse,
)
from celery.result import AsyncResult
from celery_app import start_analysis_task
from fastapi import APIRouter

router = APIRouter()


@router.post("", response_model=AnalyzeUrlResponse)
async def analyze_url(request: AnalyzeUrlRequest) -> AnalyzeUrlResponse:
    task_ids: Dict[str, str] = {}
    ks_validators_dict = process_data(request.urls)
    for url, page_data in ks_validators_dict.items():
        task = start_analysis_task.delay(
            page_data.model_dump(), request.validate_params, url
        )
        task_ids[url] = task.id
    return AnalyzeUrlResponse(task_ids=task_ids, status="processing")


@router.get("/{task_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(task_id: str) -> AnalysisResultResponse:
    task_result = AsyncResult(task_id)
    if task_result.state == "PENDING":
        return AnalysisResultResponse(status="processing", result=None)
    elif task_result.state == "SUCCESS":
        write_db(task_result)
        return AnalysisResultResponse(status="completed", result=task_result.result)
    elif task_result.state == "FAILURE":
        write_db(task_result)
        return AnalysisResultResponse(status="failed", result=None)
    else:
        return AnalysisResultResponse(status=task_result.state, result=None)
