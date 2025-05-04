from typing import Dict

from analyze.api_utils import (
    clear_task_history_user,
    create_new_tasks,
    get_tasks_by_user_token,
    process_data,
    send_task_email,
)
from analyze.schemas import (
    AnalysisResultResponse,
    AnalyzeUrlRequest,
    AnalyzeUrlResponse,
)
from api.utils import get_current_token
from celery_app import start_analysis_task
from db.dependencies import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("", response_model=AnalyzeUrlResponse)
async def analyze_url(
    request: AnalyzeUrlRequest,
    db: Session = Depends(get_db),
    token: str = Depends(get_current_token),
) -> AnalyzeUrlResponse:
    task_ids: Dict[str, str] = {}
    ks_validators_dict = process_data(request.urls)
    for url, page_data in ks_validators_dict.items():
        task = start_analysis_task.delay(
            page_data.model_dump(), request.validate_params, url
        )
        task_ids[url] = task.id
    create_new_tasks(ks_validators_dict, task_ids, db, token)
    return AnalyzeUrlResponse(task_ids=task_ids, status="processing")


@router.get("")
async def get_tasks(
    token: str = Depends(get_current_token), db: Session = Depends(get_db)
):
    tasks = await get_tasks_by_user_token(db, token)
    return tasks


@router.get("/send_task/{task_ids}")
async def send_task(
    task_ids: str,
    token: str = Depends(get_current_token),
    db: Session = Depends(get_db),
):
    send_task_email(task_ids, db, token)


@router.delete("/clear_task_history")
async def clear_task_history(
    token: str = Depends(get_current_token), db: Session = Depends(get_db)
):
    clear_task_history_user(db, token)
