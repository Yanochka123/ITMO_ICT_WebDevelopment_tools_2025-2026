from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app import models, schemas
import json

class TaskCRUD:
    """Расширенные операции с задачами"""
    
    @staticmethod
    def get_tasks_by_status(db: Session, user_id: int, status: models.TaskStatus):
        return db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.status == status,
            models.Task.is_archived == False
        ).all()
    
    @staticmethod
    def get_overdue_tasks(db: Session, user_id: int):
        """Получить просроченные задачи"""
        return db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.due_date < datetime.utcnow(),
            models.Task.status.in_([models.TaskStatus.PENDING, models.TaskStatus.IN_PROGRESS]),
            models.Task.is_archived == False
        ).all()
    
    @staticmethod
    def get_tasks_due_today(db: Session, user_id: int):
        """Задачи на сегодня"""
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        return db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.due_date >= today,
            models.Task.due_date < tomorrow,
            models.Task.status != models.TaskStatus.COMPLETED,
            models.Task.is_archived == False
        ).all()
    
    @staticmethod
    def update_task_progress(db: Session, task_id: int, progress: float):
        """Обновить прогресс задачи"""
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if task:
            task.progress = min(100, max(0, progress))
            if progress >= 100 and task.status != models.TaskStatus.COMPLETED:
                task.status = models.TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def get_task_with_time_analytics(db: Session, task_id: int):
        """Получить задачу с аналитикой времени"""
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if task:
            # Суммарное время по дням
            time_by_day = db.query(
                func.date(models.TimeEntry.start_time).label('day'),
                func.sum(models.TimeEntry.duration).label('total_time')
            ).filter(
                models.TimeEntry.task_id == task_id
            ).group_by(func.date(models.TimeEntry.start_time)).all()
            
            # Среднее время на сессию
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

class TimeTrackingCRUD:
    """Управление временем"""
    
    @staticmethod
    def start_timer(db: Session, user_id: int, task_id: int, description: str = ""):
        """Начать отсчет времени для задачи"""
        # Остановить все активные таймеры пользователя
        active_entries = db.query(models.TimeEntry).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.is_running == True
        ).all()
        
        for entry in active_entries:
            entry.is_running = False
            entry.end_time = datetime.utcnow()
            entry.duration = (entry.end_time - entry.start_time).total_seconds() / 3600
        
        # Создать новую запись времени
        new_entry = models.TimeEntry(
            task_id=task_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            is_running=True,
            description=description
        )
        db.add(new_entry)
        
        # Обновить статус задачи
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if task and task.status == models.TaskStatus.PENDING:
            task.status = models.TaskStatus.IN_PROGRESS
        
        db.commit()
        db.refresh(new_entry)
        return new_entry
    
    @staticmethod
    def stop_timer(db: Session, entry_id: int):
        """Остановить таймер"""
        entry = db.query(models.TimeEntry).filter(models.TimeEntry.id == entry_id).first()
        if entry and entry.is_running:
            entry.is_running = False
            entry.end_time = datetime.utcnow()
            entry.duration = (entry.end_time - entry.start_time).total_seconds() / 3600
            
            # Обновить общее время задачи
            task = db.query(models.Task).filter(models.Task.id == entry.task_id).first()
            if task:
                task.time_spent = db.query(func.sum(models.TimeEntry.duration)).filter(
                    models.TimeEntry.task_id == task.id
                ).scalar() or 0
            
            db.commit()
            db.refresh(entry)
        return entry
    
    @staticmethod
    def get_daily_time_summary(db: Session, user_id: int, date: datetime):
        """Получить сводку по времени за день"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        entries = db.query(models.TimeEntry).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.start_time >= start_of_day,
            models.TimeEntry.start_time < end_of_day,
            models.TimeEntry.is_running == False
        ).all()
        
        total_time = sum(e.duration for e in entries)
        
        # Группировка по задачам
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

class AnalyticsCRUD:
    """Аналитика производительности"""
    
    @staticmethod
    def get_weekly_summary(db: Session, user_id: int):
        """Еженедельная сводка"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Статистика по задачам
        task_stats = db.query(
            models.Task.status,
            func.count(models.Task.id).label('count')
        ).filter(
            models.Task.user_id == user_id,
            models.Task.created_at >= week_ago
        ).group_by(models.Task.status).all()
        
        # Время за неделю
        time_stats = db.query(
            func.sum(models.TimeEntry.duration).label('total_time')
        ).filter(
            models.TimeEntry.user_id == user_id,
            models.TimeEntry.start_time >= week_ago
        ).scalar() or 0
        
        # Продуктивность (выполненные задачи / созданные)
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
    
    @staticmethod
    def get_productivity_trend(db: Session, user_id: int, days: int = 30):
        """Тренд продуктивности"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Ежедневная статистика
        daily_stats = db.query(
            func.date(models.Task.completed_at).label('date'),
            func.count(models.Task.id).label('completed')
        ).filter(
            models.Task.user_id == user_id,
            models.Task.completed_at >= start_date
        ).group_by(func.date(models.Task.completed_at)).all()
        
        # Ежедневное время
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
    
    @staticmethod
    def get_category_breakdown(db: Session, user_id: int, start_date: datetime, end_date: datetime):
        """Распределение времени по категориям"""
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