# app/celery_app.py
import os
import httpx
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")

celery_app = Celery(
    "time_management",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.celery_app"],       # ← важно: явно указываем модуль
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)


@celery_app.task(name="parse_url")
def parse_url_task(url: str, save_to_db: bool = True):
    """Фоновая задача: вызывает parser по HTTP."""
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{PARSER_URL}/parse",
                json={"url": url, "save_to_db": save_to_db},
            )
        if response.status_code != 200:
            return {"status": "error", "url": url, "error": response.text}
        return {"status": "ok", "url": url, "result": response.json()}
    except httpx.HTTPError as e:
        return {"status": "error", "url": url, "error": str(e)}