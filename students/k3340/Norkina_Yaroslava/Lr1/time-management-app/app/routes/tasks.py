# app/routes/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import schemas, crud, models
from app.database import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[schemas.TaskResponse])
def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[models.TaskStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_tasks(db, user_id=current_user.id, skip=skip, limit=limit, status=status)


@router.get("/{task_id}", response_model=schemas.TaskDetailResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task_data = crud.get_task_with_time_analytics(db, task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_data


@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_task(db=db, task=task, user_id=current_user.id)


@router.patch("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_task = crud.update_task(db, task_id, task_update)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_task = crud.delete_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.get("/status/{status}", response_model=List[schemas.TaskResponse])
def get_tasks_by_status(
    status: models.TaskStatus,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_tasks_by_status(db, user_id=current_user.id, status=status)


@router.get("/overdue", response_model=List[schemas.TaskResponse])
def get_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_overdue_tasks(db, user_id=current_user.id)


@router.get("/due-today", response_model=List[schemas.TaskResponse])
def get_tasks_due_today(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_tasks_due_today(db, user_id=current_user.id)


@router.patch("/{task_id}/progress", response_model=schemas.TaskResponse)
def update_task_progress(
    task_id: int,
    progress: float = Query(..., ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_task = crud.update_task_progress(db, task_id, progress)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.get("/stats", response_model=schemas.TaskStatisticsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_task_stats(db, user_id=current_user.id)