# app/routes/parser.py
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from app import schemas, models
from app.routes.auth import get_current_user

from pydantic import BaseModel
from typing import Optional
from celery.result import AsyncResult
from app.celery_app import celery_app, parse_url_task

router = APIRouter(prefix="/parser", tags=["parser"])

PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")


@router.post("/parse", response_model=schemas.ParseUrlResponse)
async def parse_url(
    payload: schemas.ParseUrlRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Проксирует запрос к сервису парсера."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{PARSER_URL}/parse",
                json={"url": payload.url, "save_to_db": payload.save_to_db},
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )
        return response.json()
    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Parser service unavailable: {e}",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Parser service timed out",
        )


@router.get("/health")
async def parser_health():
    """Проверяет доступность парсера из API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{PARSER_URL}/health")
        return {
            "parser_url": PARSER_URL,
            "status_code": response.status_code,
            "body": response.json(),
        }
    except httpx.HTTPError as e:
        return {
            "parser_url": PARSER_URL,
            "status": "unavailable",
            "error": str(e),
        }


class AsyncParseResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None


@router.post("/parse/async", response_model=AsyncParseResponse)
async def parse_url_async(
    payload: schemas.ParseUrlRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Ставит задачу парсинга в очередь Celery."""
    task = parse_url_task.delay(url=payload.url, save_to_db=payload.save_to_db)
    return AsyncParseResponse(
        task_id=task.id,
        status="queued",
        message=f"Task queued for {payload.url}",
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """Возвращает статус задачи Celery."""
    result = AsyncResult(task_id, app=celery_app)
    response = TaskStatusResponse(task_id=task_id, status=result.status)
    if result.successful():
        response.result = result.result
    elif result.failed():
        response.result = {"error": str(result.result)}
    return response