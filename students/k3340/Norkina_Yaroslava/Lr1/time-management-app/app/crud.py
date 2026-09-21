import traceback
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app import models, schemas
from app.models import RecurrenceType
import json
from sqlalchemy.orm import joinedload, selectinload
from pydantic import BaseModel, Field, field_validator, model_validator

# Настройка логирования
logger = logging.getLogger(__name__)

# ===== User CRUD =====


def get_user(db: Session, user_id: int, skip: int = 0, limit: int = 100, status: Optional[models.TaskStatus] = None):
    import sys
    print(
        f"📋 get_tasks: user_id={user_id}, skip={skip}, limit={limit}, status={status}")
    sys.stdout.flush()
    try:
        return db.query(models.User).filter(models.User.id == user_id).first()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_user: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_user_by_email(db: Session, email: str):
    try:
        return db.query(models.User).filter(models.User.email == email).first()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_user_by_email: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_user_by_username(db: Session, username: str):
    try:
        return db.query(models.User).filter(models.User.username == username).first()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_user_by_username: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_user(db: Session, user: schemas.UserCreate):
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"❌ Ошибка в create_user: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

# ===== Category CRUD =====

def get_categories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    try:
        return db.query(models.Category).filter(
            models.Category.user_id == user_id
        ).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_categories: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_category(db: Session, category: schemas.CategoryCreate, user_id: int):
    try:
        db_category = models.Category(**category.model_dump(), user_id=user_id)
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except Exception as e:
        logger.error(f"❌ Ошибка в create_category: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def update_category(db: Session, category_id: int, category_update: schemas.CategoryUpdate):
    try:
        db_category = db.query(models.Category).filter(
            models.Category.id == category_id).first()
        if db_category:
            update_data = category_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_category, field, value)
            db.commit()
            db.refresh(db_category)
        return db_category
    except Exception as e:
        logger.error(f"❌ Ошибка в update_category: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def delete_category(db: Session, category_id: int):
    try:
        db_category = db.query(models.Category).filter(
            models.Category.id == category_id).first()
        if db_category:
            db.delete(db_category)
            db.commit()
        return db_category
    except Exception as e:
        logger.error(f"❌ Ошибка в delete_category: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

# ===== Tag CRUD =====

def get_tags(db: Session, user_id: int):
    try:
        return db.query(models.Tag).filter(models.Tag.user_id == user_id).all()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_tags: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_tag(db: Session, tag: schemas.TagCreate, user_id: int):
    try:
        db_tag = models.Tag(**tag.model_dump(), user_id=user_id)
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return db_tag
    except Exception as e:
        logger.error(f"❌ Ошибка в create_tag: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def update_tag(db: Session, tag_id: int, tag_update: schemas.TagUpdate):
    try:
        db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
        if db_tag:
            update_data = tag_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_tag, field, value)
            db.commit()
            db.refresh(db_tag)
        return db_tag
    except Exception as e:
        logger.error(f"❌ Ошибка в update_tag: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def delete_tag(db: Session, tag_id: int):
    try:
        db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
        if db_tag:
            db.delete(db_tag)
            db.commit()
        return db_tag
    except Exception as e:
        logger.error(f"❌ Ошибка в delete_tag: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 100, status: Optional[models.TaskStatus] = None):
    """Получение списка задач с загрузкой всех связей"""
    print(
        f"📋 get_tasks: user_id={user_id}, skip={skip}, limit={limit}, status={status}")

    query = db.query(models.Task).options(
        joinedload(models.Task.category),           # many-to-one
        selectinload(models.Task.tags),             # коллекция
        selectinload(models.Task.subtasks),         # коллекция
        selectinload(models.Task.time_entries)      # коллекция
    ).filter(
        models.Task.user_id == user_id,
        models.Task.is_archived == False
    )

    if status:
        query = query.filter(models.Task.status == status)

    tasks = query.offset(skip).limit(limit).all()

    print(f"Найдено задач: {len(tasks)}")
    return tasks

def get_task(db: Session, task_id: int, user_id: int):
    """Получение задачи по ID"""
    try:
        print(f"📋 get_task: task_id={task_id}, user_id={user_id}")
        result = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.user_id == user_id
        ).first()
        print(f"✅ Задача найдена: {result is not None}")
        return result
    except Exception as e:
        print(f"❌ Ошибка в get_task: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в get_task: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    try:
        print(f"create_task: user_id={user_id}")

        task_data = task.model_dump(exclude={'tag_ids'})

        if task_data.get('category_id') == 0:
            task_data['category_id'] = None
        if task_data.get('parent_task_id') == 0:
            task_data['parent_task_id'] = None

        db_task = models.Task(**task_data, user_id=user_id)

        if task.tag_ids:
            tags = db.query(models.Tag).filter(
                models.Tag.id.in_(task.tag_ids)).all()
            db_task.tags = tags

        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # Загружаем задачу со всеми связями
        created_task = db.query(models.Task).options(
            joinedload(models.Task.category),
            selectinload(models.Task.tags),
            selectinload(models.Task.subtasks),
            selectinload(models.Task.time_entries)
        ).filter(models.Task.id == db_task.id).first()

        print(
            f"Задача создана с ID: {created_task.id if created_task else db_task.id}")
        return created_task or db_task

    except Exception as e:
        print(f"Ошибка в create_task: {str(e)}")
        traceback.print_exc()
        db.rollback()
        raise

def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    try:
        print(f"📝 update_task: task_id={task_id}")
        print(f"📝 Данные обновления: {task_update.model_dump()}")

        db_task = db.query(models.Task).filter(
            models.Task.id == task_id).first()
        if not db_task:
            print("❌ Задача не найдена")
            return None

        update_data = task_update.model_dump(
            exclude_unset=True, exclude={'tag_ids'})

        if 'status' in update_data and update_data['status'] == models.TaskStatus.COMPLETED:
            db_task.completed_at = datetime.utcnow()
            print("📝 Задача помечена как выполненная")

        for field, value in update_data.items():
            setattr(db_task, field, value)
            print(f"📝 Обновлено поле {field} = {value}")

        if 'tag_ids' in task_update.model_dump(exclude_unset=True):
            if task_update.tag_ids is not None:
                tags = db.query(models.Tag).filter(
                    models.Tag.id.in_(task_update.tag_ids)).all()
                db_task.tags = tags
                print(f"📝 Обновлены теги: {[t.id for t in tags]}")

        db_task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_task)
        print(f"✅ Задача {task_id} обновлена")

        return db_task
    except Exception as e:
        print(f"❌ Ошибка в update_task: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в update_task: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def delete_task(db: Session, task_id: int):
    try:
        print(f"📝 delete_task: task_id={task_id}")
        db_task = db.query(models.Task).filter(
            models.Task.id == task_id).first()
        if db_task:
            db.delete(db_task)
            db.commit()
            print(f"✅ Задача {task_id} удалена")
        return db_task
    except Exception as e:
        print(f"❌ Ошибка в delete_task: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в delete_task: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def get_tasks_by_status(db: Session, user_id: int, status: models.TaskStatus):
    try:
        print(f"📋 get_tasks_by_status: user_id={user_id}, status={status}")
        result = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.status == status,
            models.Task.is_archived == False
        ).all()
        print(f"✅ Найдено задач: {len(result)}")
        return result
    except Exception as e:
        print(f"❌ Ошибка в get_tasks_by_status: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в get_tasks_by_status: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_overdue_tasks(db: Session, user_id: int):
    try:
        print(f"📋 get_overdue_tasks: user_id={user_id}")
        now = datetime.utcnow()
        result = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.due_date < now,
            models.Task.status.in_(
                [models.TaskStatus.PENDING, models.TaskStatus.IN_PROGRESS]),
            models.Task.is_archived == False
        ).all()
        print(f"✅ Найдено просроченных задач: {len(result)}")
        return result
    except Exception as e:
        print(f"❌ Ошибка в get_overdue_tasks: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в get_overdue_tasks: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_tasks_due_today(db: Session, user_id: int):
    try:
        print(f"📋 get_tasks_due_today: user_id={user_id}")
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        result = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.due_date >= today,
            models.Task.due_date < tomorrow,
            models.Task.status != models.TaskStatus.COMPLETED,
            models.Task.is_archived == False
        ).all()
        print(f"✅ Найдено задач на сегодня: {len(result)}")
        return result
    except Exception as e:
        print(f"❌ Ошибка в get_tasks_due_today: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в get_tasks_due_today: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def update_task_progress(db: Session, task_id: int, progress: float):
    try:
        print(
            f"📝 update_task_progress: task_id={task_id}, progress={progress}")
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if task:
            task.progress = min(100, max(0, progress))
            if progress >= 100 and task.status != models.TaskStatus.COMPLETED:
                task.status = models.TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                print("✅ Задача выполнена!")
            db.commit()
            db.refresh(task)
            print(f"✅ Прогресс обновлен: {task.progress}%")
        return task
    except Exception as e:
        print(f"❌ Ошибка в update_task_progress: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в update_task_progress: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise


def get_task_with_time_analytics(db: Session, task_id: int):
    """Получение задачи с аналитикой времени"""
    from datetime import datetime

    task = db.query(models.Task).options(
        joinedload(models.Task.category),
        selectinload(models.Task.tags),
        selectinload(models.Task.subtasks),
        selectinload(models.Task.time_entries)
    ).filter(models.Task.id == task_id).first()
    if not task:
        return None

    # Получаем аналитику времени
    time_by_day = db.query(
        func.date(models.TimeEntry.start_time).label('day'),
        func.sum(models.TimeEntry.duration).label('total_time')
    ).filter(
        models.TimeEntry.task_id == task_id
    ).group_by(func.date(models.TimeEntry.start_time)).all()

    avg_session = db.query(
        func.avg(models.TimeEntry.duration)
    ).filter(models.TimeEntry.task_id == task_id).scalar() or 0

    total_sessions = db.query(models.TimeEntry).filter(
        models.TimeEntry.task_id == task_id
    ).count()

    total_time_spent = task.time_spent or 0
    estimated_vs_actual = (
        total_time_spent / task.estimated_time * 100) if task.estimated_time > 0 else 0
    efficiency_score = estimated_vs_actual

    # Преобразуем time_by_day в список словарей
    time_by_day_list = []
    for item in time_by_day:
        if hasattr(item, 'day') and hasattr(item, 'total_time'):
            day_str = item.day.isoformat() if hasattr(
                item.day, 'isoformat') else str(item.day)
            time_by_day_list.append({
                'day': day_str,
                'total_time': item.total_time or 0
            })

    # Создаем объект, который будет соответствовать TaskDetailResponse
    # Добавляем аналитические поля прямо в объект task
    task.total_time_spent = total_time_spent
    task.estimated_vs_actual = estimated_vs_actual
    task.time_by_day = time_by_day_list
    task.avg_session_time = avg_session or 0
    task.total_sessions = total_sessions
    task.efficiency_score = efficiency_score

    return task

def get_task_stats(db: Session, user_id: int):
    try:
        print(f"📋 get_task_stats: user_id={user_id}")
        total = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.is_archived == False
        ).count()

        completed = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.status == models.TaskStatus.COMPLETED
        ).count()

        in_progress = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.status == models.TaskStatus.IN_PROGRESS
        ).count()

        pending = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.status == models.TaskStatus.PENDING
        ).count()

        overdue = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.due_date < datetime.utcnow(),
            models.Task.status.in_(
                [models.TaskStatus.PENDING, models.TaskStatus.IN_PROGRESS])
        ).count()

        total_time = db.query(func.sum(models.TimeEntry.duration)).filter(
            models.TimeEntry.user_id == user_id
        ).scalar() or 0

        by_priority = {}
        for priority in models.PriorityLevel:
            count = db.query(models.Task).filter(
                models.Task.user_id == user_id,
                models.Task.priority == priority
            ).count()
            by_priority[priority.value] = count

        print(
            f"✅ Статистика: total={total}, completed={completed}, in_progress={in_progress}")

        return schemas.TaskStatisticsResponse(
            total_tasks=total,
            completed_tasks=completed,
            in_progress_tasks=in_progress,
            pending_tasks=pending,
            overdue_tasks=overdue,
            completion_rate=round((completed / total * 100)
                                  if total > 0 else 0, 2),
            total_time_spent=total_time,
            tasks_by_priority=by_priority
        )
    except Exception as e:
        print(f"❌ Ошибка в get_task_stats: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"❌ Ошибка в get_task_stats: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# ===== TimeEntry CRUD =====

def get_time_entries(db: Session, user_id: int, task_id: Optional[int] = None):
    try:
        query = db.query(models.TimeEntry).filter(
            models.TimeEntry.user_id == user_id)
        if task_id:
            query = query.filter(models.TimeEntry.task_id == task_id)
        return query.order_by(desc(models.TimeEntry.start_time)).all()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_time_entries: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_time_entry(db: Session, time_entry: schemas.TimeEntryCreate, user_id: int):
    try:
        db_entry = models.TimeEntry(**time_entry.model_dump(), user_id=user_id)
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry
    except Exception as e:
        logger.error(f"❌ Ошибка в create_time_entry: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def update_time_entry(db: Session, entry_id: int, entry_update: schemas.TimeEntryUpdate):
    try:
        db_entry = db.query(models.TimeEntry).filter(
            models.TimeEntry.id == entry_id).first()
        if db_entry:
            update_data = entry_update.model_dump(exclude_unset=True)
            if 'end_time' in update_data and db_entry.start_time:
                db_entry.duration = (
                    update_data['end_time'] - db_entry.start_time).total_seconds() / 3600
            for field, value in update_data.items():
                setattr(db_entry, field, value)
            db.commit()
            db.refresh(db_entry)
        return db_entry
    except Exception as e:
        logger.error(f"❌ Ошибка в update_time_entry: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def delete_time_entry(db: Session, entry_id: int):
    try:
        db_entry = db.query(models.TimeEntry).filter(
            models.TimeEntry.id == entry_id).first()
        if db_entry:
            db.delete(db_entry)
            db.commit()
        return db_entry
    except Exception as e:
        logger.error(f"❌ Ошибка в delete_time_entry: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def start_timer(db: Session, user_id: int, task_id: int, description: str = ""):
    try:
        active_entries = db.query(models.TimeEntry).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.is_running == True
        ).all()

        for entry in active_entries:
            entry.is_running = False
            entry.end_time = datetime.utcnow()
            entry.duration = (
                entry.end_time - entry.start_time).total_seconds() / 3600

        new_entry = models.TimeEntry(
            task_id=task_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            is_running=True,
            description=description
        )
        db.add(new_entry)

        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if task and task.status == models.TaskStatus.PENDING:
            task.status = models.TaskStatus.IN_PROGRESS

        db.commit()
        db.refresh(new_entry)
        return new_entry
    except Exception as e:
        logger.error(f"❌ Ошибка в start_timer: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def stop_timer(db: Session, entry_id: int):
    try:
        entry = db.query(models.TimeEntry).filter(
            models.TimeEntry.id == entry_id).first()
        if entry and entry.is_running:
            entry.is_running = False
            entry.end_time = datetime.utcnow()
            entry.duration = (
                entry.end_time - entry.start_time).total_seconds() / 3600

            task = db.query(models.Task).filter(
                models.Task.id == entry.task_id).first()
            if task:
                task.time_spent = db.query(func.sum(models.TimeEntry.duration)).filter(
                    models.TimeEntry.task_id == task.id
                ).scalar() or 0

            db.commit()
            db.refresh(entry)
        return entry
    except Exception as e:
        logger.error(f"❌ Ошибка в stop_timer: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def get_daily_time_summary(db: Session, user_id: int, date: datetime):
    try:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        entries = db.query(models.TimeEntry).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.start_time >= start_of_day,
            models.TimeEntry.start_time < end_of_day,
            models.TimeEntry.is_running == False
        ).all()

        total_time = sum(e.duration for e in entries)

        by_task = db.query(
            models.Task.title,
            func.sum(models.TimeEntry.duration).label('total_time')
        ).join(
            models.TimeEntry, models.TimeEntry.task_id == models.Task.id
        ).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.start_time >= start_of_day,
            models.TimeEntry.start_time < end_of_day
        ).group_by(models.Task.id).all()

        return {
            "total_time": total_time,
            "by_task": [{"task": t.title, "time": t.total_time} for t in by_task],
            "entry_count": len(entries)
        }
    except Exception as e:
        logger.error(f"❌ Ошибка в get_daily_time_summary: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# ===== Остальные CRUD функции (с отладкой) =====

def get_weekly_summary(db: Session, user_id: int):
    try:
        week_ago = datetime.utcnow() - timedelta(days=7)

        task_stats = db.query(
            models.Task.status,
            func.count(models.Task.id).label('count')
        ).filter(
            models.Task.user_id == user_id,
            models.Task.created_at >= week_ago
        ).group_by(models.Task.status).all()

        time_stats = db.query(
            func.sum(models.TimeEntry.duration).label('total_time')
        ).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.start_time >= week_ago
        ).scalar() or 0

        created = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.created_at >= week_ago
        ).count()

        completed = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.completed_at >= week_ago
        ).count()

        productivity = (completed / created * 100) if created > 0 else 0

        return {
            "period": "weekly",
            "tasks": {stat.status.value: stat.count for stat in task_stats},
            "total_time": time_stats,
            "productivity": round(productivity, 2),
            "tasks_created": created,
            "tasks_completed": completed
        }
    except Exception as e:
        logger.error(f"❌ Ошибка в get_weekly_summary: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_productivity_trend(db: Session, user_id: int, days: int = 30):
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        daily_stats = db.query(
            func.date(models.Task.completed_at).label('date'),
            func.count(models.Task.id).label('completed')
        ).filter(
            models.Task.user_id == user_id,
            models.Task.completed_at >= start_date
        ).group_by(func.date(models.Task.completed_at)).all()

        daily_time = db.query(
            func.date(models.TimeEntry.start_time).label('date'),
            func.sum(models.TimeEntry.duration).label('time')
        ).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.start_time >= start_date
        ).group_by(func.date(models.TimeEntry.start_time)).all()

        return {
            "daily_completed": [{"date": s.date, "count": s.completed} for s in daily_stats],
            "daily_time": [{"date": t.date, "hours": t.time} for t in daily_time]
        }
    except Exception as e:
        logger.error(f"❌ Ошибка в get_productivity_trend: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_category_breakdown(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    try:
        results = db.query(
            models.Category.name,
            models.Category.color,
            func.sum(models.TimeEntry.duration).label('total_time')
        ).join(
            models.Task, models.Task.category_id == models.Category.id
        ).join(
            models.TimeEntry, models.TimeEntry.task_id == models.Task.id
        ).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.start_time >= start_date,
            models.TimeEntry.start_time <= end_date,
            models.TimeEntry.is_running == False
        ).group_by(models.Category.id).all()

        total = sum(r.total_time for r in results)

        return {
            "categories": [
                {
                    "name": r.name,
                    "color": r.color,
                    "time": r.total_time,
                    "percentage": (r.total_time / total * 100) if total > 0 else 0
                }
                for r in results
            ],
            "total_time": total
        }
    except Exception as e:
        logger.error(f"❌ Ошибка в get_category_breakdown: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_daily_schedules(db: Session, user_id: int, date: Optional[datetime] = None):
    try:
        query = db.query(models.DailySchedule).filter(
            models.DailySchedule.user_id == user_id)
        if date:
            start_of_day = date.replace(
                hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.filter(
                models.DailySchedule.date >= start_of_day,
                models.DailySchedule.date < end_of_day
            )
        return query.order_by(models.DailySchedule.date).all()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_daily_schedules: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_daily_schedule(db: Session, schedule: schemas.DailyScheduleCreate, user_id: int):
    try:
        db_schedule = models.DailySchedule(
            **schedule.model_dump(),
            user_id=user_id,
            day_of_week=schedule.date.weekday()
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return db_schedule
    except Exception as e:
        logger.error(f"❌ Ошибка в create_daily_schedule: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def update_daily_schedule(db: Session, schedule_id: int, schedule_update: schemas.DailyScheduleUpdate):
    try:
        db_schedule = db.query(models.DailySchedule).filter(
            models.DailySchedule.id == schedule_id).first()
        if db_schedule:
            update_data = schedule_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_schedule, field, value)
            db.commit()
            db.refresh(db_schedule)
        return db_schedule
    except Exception as e:
        logger.error(f"❌ Ошибка в update_daily_schedule: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def delete_daily_schedule(db: Session, schedule_id: int):
    try:
        db_schedule = db.query(models.DailySchedule).filter(
            models.DailySchedule.id == schedule_id).first()
        if db_schedule:
            db.delete(db_schedule)
            db.commit()
        return db_schedule
    except Exception as e:
        logger.error(f"❌ Ошибка в delete_daily_schedule: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def get_notifications(db: Session, user_id: int, is_read: Optional[bool] = None):
    try:
        query = db.query(models.Notification).filter(
            models.Notification.user_id == user_id)
        if is_read is not None:
            query = query.filter(models.Notification.is_read == is_read)
        return query.order_by(desc(models.Notification.created_at)).all()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_notifications: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_notification(db: Session, notification: schemas.NotificationCreate, user_id: int):
    try:
        db_notification = models.Notification(
            **notification.model_dump(), user_id=user_id)
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        return db_notification
    except Exception as e:
        logger.error(f"❌ Ошибка в create_notification: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def update_notification(db: Session, notification_id: int, notification_update: schemas.NotificationUpdate):
    try:
        db_notification = db.query(models.Notification).filter(
            models.Notification.id == notification_id).first()
        if db_notification:
            update_data = notification_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_notification, field, value)
            db.commit()
            db.refresh(db_notification)
        return db_notification
    except Exception as e:
        logger.error(f"❌ Ошибка в update_notification: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

def mark_notification_read(db: Session, notification_id: int):
    try:
        db_notification = db.query(models.Notification).filter(
            models.Notification.id == notification_id).first()
        if db_notification:
            db_notification.is_read = True
            db_notification.read_at = datetime.utcnow()
            db.commit()
            db.refresh(db_notification)
        return db_notification
    except Exception as e:
        logger.error(f"❌ Ошибка в mark_notification_read: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise

# ===== User CRUD (дополнение) =====


def get_all_users(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    try:
        query = db.query(models.User)
        if search:
            query = query.filter(
                (models.User.username.ilike(f"%{search}%")) |
                (models.User.email.ilike(f"%{search}%"))
            )
        return query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"❌ Ошибка в get_all_users: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def count_users(db: Session, search: Optional[str] = None):
    try:
        query = db.query(models.User)
        if search:
            query = query.filter(
                (models.User.username.ilike(f"%{search}%")) |
                (models.User.email.ilike(f"%{search}%"))
            )
        return query.count()
    except Exception as e:
        logger.error(f"❌ Ошибка в count_users: {str(e)}")
        logger.error(traceback.format_exc())
        raise
