# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app import models, schemas
import json

# ===== User CRUD =====


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
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

# ===== Category CRUD =====


def get_categories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Category).filter(
        models.Category.user_id == user_id
    ).offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate, user_id: int):
    db_category = models.Category(**category.model_dump(), user_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category_update: schemas.CategoryUpdate):
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id).first()
    if db_category:
        update_data = category_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        db.commit()
        db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id).first()
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category

# ===== Tag CRUD =====


def get_tags(db: Session, user_id: int):
    return db.query(models.Tag).filter(models.Tag.user_id == user_id).all()


def create_tag(db: Session, tag: schemas.TagCreate, user_id: int):
    db_tag = models.Tag(**tag.model_dump(), user_id=user_id)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def update_tag(db: Session, tag_id: int, tag_update: schemas.TagUpdate):
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if db_tag:
        update_data = tag_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tag, field, value)
        db.commit()
        db.refresh(db_tag)
    return db_tag


def delete_tag(db: Session, tag_id: int):
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if db_tag:
        db.delete(db_tag)
        db.commit()
    return db_tag

# ===== Task CRUD =====


def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 100, status: Optional[models.TaskStatus] = None):
    query = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.is_archived == False
    )
    if status:
        query = query.filter(models.Task.status == status)
    return query.offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int, user_id: int):
    return db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()


def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    task_data = task.model_dump(exclude={'tag_ids'})
    db_task = models.Task(**task_data, user_id=user_id)

    if task.tag_ids:
        tags = db.query(models.Tag).filter(
            models.Tag.id.in_(task.tag_ids)).all()
        db_task.tags = tags

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        update_data = task_update.model_dump(
            exclude_unset=True, exclude={'tag_ids'})

        if 'status' in update_data and update_data['status'] == models.TaskStatus.COMPLETED:
            db_task.completed_at = datetime.utcnow()

        for field, value in update_data.items():
            setattr(db_task, field, value)

        if 'tag_ids' in task_update.model_dump(exclude_unset=True):
            if task_update.tag_ids is not None:
                tags = db.query(models.Tag).filter(
                    models.Tag.id.in_(task_update.tag_ids)).all()
                db_task.tags = tags

        db_task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task


def get_tasks_by_status(db: Session, user_id: int, status: models.TaskStatus):
    return db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.status == status,
        models.Task.is_archived == False
    ).all()


def get_overdue_tasks(db: Session, user_id: int):
    return db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.due_date < datetime.utcnow(),
        models.Task.status.in_(
            [models.TaskStatus.PENDING, models.TaskStatus.IN_PROGRESS]),
        models.Task.is_archived == False
    ).all()


def get_tasks_due_today(db: Session, user_id: int):
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    return db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.due_date >= today,
        models.Task.due_date < tomorrow,
        models.Task.status != models.TaskStatus.COMPLETED,
        models.Task.is_archived == False
    ).all()


def update_task_progress(db: Session, task_id: int, progress: float):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.progress = min(100, max(0, progress))
        if progress >= 100 and task.status != models.TaskStatus.COMPLETED:
            task.status = models.TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return task


def get_task_with_time_analytics(db: Session, task_id: int):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        time_by_day = db.query(
            func.date(models.TimeEntry.start_time).label('day'),
            func.sum(models.TimeEntry.duration).label('total_time')
        ).filter(
            models.TimeEntry.task_id == task_id
        ).group_by(func.date(models.TimeEntry.start_time)).all()

        avg_session = db.query(
            func.avg(models.TimeEntry.duration)
        ).filter(models.TimeEntry.task_id == task_id).scalar() or 0

        return {
            "task": task,
            "time_by_day": [{"day": d.day, "total_time": d.total_time} for d in time_by_day],
            "avg_session_time": avg_session,
            "total_sessions": len(task.time_entries),
            "efficiency_score": (task.time_spent / task.estimated_time * 100) if task.estimated_time > 0 else 0
        }
    return None


def get_task_stats(db: Session, user_id: int):
    total = db.query(models.Task).filter(models.Task.user_id ==
                                         user_id, models.Task.is_archived == False).count()
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

# ===== TimeEntry CRUD =====


def get_time_entries(db: Session, user_id: int, task_id: Optional[int] = None):
    query = db.query(models.TimeEntry).filter(
        models.TimeEntry.user_id == user_id)
    if task_id:
        query = query.filter(models.TimeEntry.task_id == task_id)
    return query.order_by(desc(models.TimeEntry.start_time)).all()


def create_time_entry(db: Session, time_entry: schemas.TimeEntryCreate, user_id: int):
    db_entry = models.TimeEntry(**time_entry.model_dump(), user_id=user_id)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def update_time_entry(db: Session, entry_id: int, entry_update: schemas.TimeEntryUpdate):
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


def delete_time_entry(db: Session, entry_id: int):
    db_entry = db.query(models.TimeEntry).filter(
        models.TimeEntry.id == entry_id).first()
    if db_entry:
        db.delete(db_entry)
        db.commit()
    return db_entry


def start_timer(db: Session, user_id: int, task_id: int, description: str = ""):
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


def stop_timer(db: Session, entry_id: int):
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


def get_daily_time_summary(db: Session, user_id: int, date: datetime):
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

# ===== Analytics CRUD =====


def get_weekly_summary(db: Session, user_id: int):
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


def get_productivity_trend(db: Session, user_id: int, days: int = 30):
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


def get_category_breakdown(db: Session, user_id: int, start_date: datetime, end_date: datetime):
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

# ===== Schedule CRUD =====


def get_daily_schedules(db: Session, user_id: int, date: Optional[datetime] = None):
    query = db.query(models.DailySchedule).filter(
        models.DailySchedule.user_id == user_id)
    if date:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        query = query.filter(
            models.DailySchedule.date >= start_of_day,
            models.DailySchedule.date < end_of_day
        )
    return query.order_by(models.DailySchedule.date).all()


def create_daily_schedule(db: Session, schedule: schemas.DailyScheduleCreate, user_id: int):
    db_schedule = models.DailySchedule(
        **schedule.model_dump(),
        user_id=user_id,
        day_of_week=schedule.date.weekday()
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def update_daily_schedule(db: Session, schedule_id: int, schedule_update: schemas.DailyScheduleUpdate):
    db_schedule = db.query(models.DailySchedule).filter(
        models.DailySchedule.id == schedule_id).first()
    if db_schedule:
        update_data = schedule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)
        db.commit()
        db.refresh(db_schedule)
    return db_schedule


def delete_daily_schedule(db: Session, schedule_id: int):
    db_schedule = db.query(models.DailySchedule).filter(
        models.DailySchedule.id == schedule_id).first()
    if db_schedule:
        db.delete(db_schedule)
        db.commit()
    return db_schedule

# ===== Notification CRUD =====


def get_notifications(db: Session, user_id: int, is_read: Optional[bool] = None):
    query = db.query(models.Notification).filter(
        models.Notification.user_id == user_id)
    if is_read is not None:
        query = query.filter(models.Notification.is_read == is_read)
    return query.order_by(desc(models.Notification.created_at)).all()


def create_notification(db: Session, notification: schemas.NotificationCreate, user_id: int):
    db_notification = models.Notification(
        **notification.model_dump(), user_id=user_id)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def update_notification(db: Session, notification_id: int, notification_update: schemas.NotificationUpdate):
    db_notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id).first()
    if db_notification:
        update_data = notification_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_notification, field, value)
        db.commit()
        db.refresh(db_notification)
    return db_notification


def mark_notification_read(db: Session, notification_id: int):
    db_notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id).first()
    if db_notification:
        db_notification.is_read = True
        db_notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(db_notification)
    return db_notification
