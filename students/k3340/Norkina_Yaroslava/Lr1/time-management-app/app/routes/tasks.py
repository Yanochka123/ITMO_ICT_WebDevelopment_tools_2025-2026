# app/routes/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
from app import schemas, crud, models
from app.database import get_db
from app.routes.auth import get_current_user
from app.debug import log_error
import traceback
import sys

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[schemas.TaskResponse])
def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[models.TaskStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить список задач с пагинацией и фильтрацией"""
    try:
        print("GET /tasks/ вызван")
        print(f"Пользователь: {current_user.id}")

        tasks = crud.get_tasks(db, user_id=current_user.id,
                               skip=skip, limit=limit, status=status)

        print(f"Возвращено {len(tasks)} задач")
        return tasks

    except Exception as e:
        print(f"ОШИБКА В GET /tasks/")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "traceback": traceback.format_exc()}
        )


@router.get("/stats", response_model=schemas.TaskStatisticsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print("🚀 GET /tasks/stats вызван")
        sys.stdout.flush()
        return crud.get_task_stats(db, user_id=current_user.id)
    except Exception as e:
        log_error(f"Ошибка в GET /tasks/stats: {str(e)}", exc_info=True)
        raise


@router.get("/overdue", response_model=List[schemas.TaskResponse])
def get_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print("🚀 GET /tasks/overdue вызван")
        sys.stdout.flush()
        return crud.get_overdue_tasks(db, user_id=current_user.id)
    except Exception as e:
        log_error(f"Ошибка в GET /tasks/overdue: {str(e)}", exc_info=True)
        raise


@router.get("/due-today", response_model=List[schemas.TaskResponse])
def get_tasks_due_today(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print("🚀 GET /tasks/due-today вызван")
        sys.stdout.flush()
        return crud.get_tasks_due_today(db, user_id=current_user.id)
    except Exception as e:
        log_error(f"Ошибка в GET /tasks/due-today: {str(e)}", exc_info=True)
        raise

@router.get("/status/{status}", response_model=List[schemas.TaskResponse])
def get_tasks_by_status(
    status: models.TaskStatus,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print(f"🚀 GET /tasks/status/{status} вызван")
        sys.stdout.flush()
        return crud.get_tasks_by_status(db, user_id=current_user.id, status=status)
    except Exception as e:
        log_error(
            f"Ошибка в GET /tasks/status/{status}: {str(e)}", exc_info=True)
        raise


# app/routes/tasks.py
@router.get("/{task_id}", response_model=schemas.TaskDetailResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print(f"GET /tasks/{task_id} вызван")
        task = crud.get_task_with_time_analytics(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


@router.post("/", response_model=schemas.TaskCreateResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новую задачу"""
    try:
        print(" POST /tasks/ вызван")
        print(f" Пользователь: {current_user.id}")
        print(f" Данные задачи: {task.model_dump()}")

        task_data = task.model_dump(exclude={'tag_ids'})

        if task_data.get('category_id') == 0:
            task_data['category_id'] = None
        if task_data.get('parent_task_id') == 0:
            task_data['parent_task_id'] = None

        db_task = models.Task(**task_data, user_id=current_user.id)

        if task.tag_ids:
            tags = db.query(models.Tag).filter(
                models.Tag.id.in_(task.tag_ids)).all()
            db_task.tags = tags

        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # Загружаем задачу со всеми связями для ответа
        created_task = db.query(models.Task).options(
            joinedload(models.Task.category),
            selectinload(models.Task.tags),
            selectinload(models.Task.subtasks),
            selectinload(models.Task.time_entries)
        ).filter(models.Task.id == db_task.id).first()

        print(f" Задача создана с ID: {db_task.id}")
        return created_task or db_task

    except Exception as e:
        print(f" ОШИБКА В POST /tasks/")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print(f"🚀 PATCH /tasks/{task_id} вызван")
        sys.stdout.flush()
        db_task = crud.update_task(db, task_id, task_update)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        return db_task
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка в PATCH /tasks/{task_id}: {str(e)}", exc_info=True)
        raise

@router.patch("/{task_id}/progress", response_model=schemas.TaskResponse)
def update_task_progress(
    task_id: int,
    progress: float = Query(..., ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print(f"🚀 PATCH /tasks/{task_id}/progress?progress={progress} вызван")
        sys.stdout.flush()
        db_task = crud.update_task_progress(db, task_id, progress)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        return db_task
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            f"Ошибка в PATCH /tasks/{task_id}/progress: {str(e)}", exc_info=True)
        raise


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print(f"🚀 DELETE /tasks/{task_id} вызван")
        sys.stdout.flush()
        db_task = crud.delete_task(db, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка в DELETE /tasks/{task_id}: {str(e)}", exc_info=True)
        raise
