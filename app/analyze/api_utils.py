import json
from datetime import datetime
from typing import Dict

from analyze.schemas import KSAttributes
from analyze.scraper import FilesProcessor, ParserWeb
from auth.utils import send_task_to_user_email
from celery.result import AsyncResult
from db.models import TaskHistory, User
from sqlalchemy.orm import Session


def process_data(urls):
    ks_validators_dict = {}
    for url in urls:
        page_data = ParserWeb(url).fetch_and_parse()
        page_data = FilesProcessor().generate_parsed_files_data(page_data)
        ks_validators_dict[url] = page_data
    return ks_validators_dict


def create_new_tasks(
    ks_validators_dict: Dict[str, KSAttributes],
    task_ids: Dict[str, str],
    db: Session,
    token: str,
):
    user = db.query(User).filter(User.token == token).first()

    for url, attributes in ks_validators_dict.items():
        new_task = TaskHistory(
            user_id=user.id,
            ids=task_ids[url],
            url=url,
            description=attributes.name,
            status="PENDING",
        )
        db.add(new_task)
    db.commit()


async def process_task(user_id: int, db: Session):
    user_tasks = db.query(TaskHistory).filter(TaskHistory.user_id == user_id).all()
    for task in user_tasks:
        task_result = AsyncResult(task.ids)
        task.status = task_result.status
        if task_result.state == "SUCCESS" and not task.completed_at:
            result = json.dumps(task_result.result)
            task.result = result
            task.completed_at = datetime.now()
        task.status = task_result.state
        db.commit()


async def get_tasks_by_user_token(db: Session, token: str):
    user = db.query(User).filter(User.token == token).first()
    user_id = user.id
    await process_task(user_id=user_id, db=db)
    user_tasks = db.query(TaskHistory).filter(TaskHistory.user_id == user_id).all()
    return user_tasks


def send_task_email(ids: str, db: Session, token: str):
    user = db.query(User).filter(User.token == token).first()
    task = (
        db.query(TaskHistory)
        .filter(TaskHistory.user_id == user.id, TaskHistory.ids == ids)
        .first()
    )
    send_task_to_user_email(user.email, task)


def clear_task_history_user(db: Session, token: str):
    user = db.query(User).filter(User.token == token).first()
    db.query(TaskHistory).filter(TaskHistory.user_id == user.id).delete()
    db.commit()
