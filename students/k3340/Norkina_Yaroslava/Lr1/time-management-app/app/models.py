# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text, Enum, Table, Time, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

# Enum для статусов задач
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

# Enum для приоритетов
class PriorityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

# Enum для повторяющихся задач
class RecurrenceType(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

# Ассоциативная таблица для связи задач с тегами
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(255))
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    
    # Отношения
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="owner", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="owner", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="user", cascade="all, delete-orphan")
    daily_schedules = relationship("DailySchedule", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    recurring_tasks = relationship("RecurringTask", back_populates="user", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7), default="#667eea")
    icon = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    owner = relationship("User", back_populates="categories")
    tasks = relationship("Task", back_populates="category")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), nullable=False)
    color = Column(String(7), default="#6c757d")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    owner = relationship("User", back_populates="tags")
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.MEDIUM)
    priority_score = Column(Integer, default=3)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    reminder_date = Column(DateTime, nullable=True)
    
    estimated_time = Column(Float, default=0.0)
    time_spent = Column(Float, default=0.0)
    time_allocated = Column(Float, default=0.0)
    
    progress = Column(Float, default=0.0)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(Enum(RecurrenceType), default=RecurrenceType.NONE)

    is_archived = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE'), nullable=False)
    category_id = Column(Integer, ForeignKey(
        "categories.id", ondelete='SET NULL'), nullable=True)
    parent_task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete='CASCADE'), nullable=True)

    owner = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")
    recurring_task = relationship("RecurringTask", back_populates="task", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_tasks_user_status', 'user_id', 'status'),
        Index('ix_tasks_user_due_date', 'user_id', 'due_date'),
        Index('ix_tasks_user_priority', 'user_id', 'priority_score'),
    )

class TimeEntry(Base):
    __tablename__ = "time_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, default=0.0)
    description = Column(Text)
    is_running = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", back_populates="time_entries")
    user = relationship("User", back_populates="time_entries")


class RecurringTask(Base):
    __tablename__ = "recurring_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete='CASCADE'), unique=True)
    recurrence_type = Column(Enum(RecurrenceType), nullable=False)
    interval = Column(Integer, default=1)
    end_date = Column(DateTime, nullable=True)
    max_occurrences = Column(Integer, nullable=True)
    current_occurrence = Column(Integer, default=0)
    last_generated = Column(DateTime, nullable=True)
    next_generation = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    user = relationship("User", back_populates="recurring_tasks")
    task = relationship("Task", back_populates="recurring_task")

class DailySchedule(Base):
    __tablename__ = "daily_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    
    date = Column(DateTime, nullable=False, index=True)
    day_of_week = Column(Integer)

    work_start = Column(Time, default="09:00:00")
    work_end = Column(Time, default="18:00:00")
    lunch_start = Column(Time, nullable=True)
    lunch_end = Column(Time, nullable=True)
    break_duration = Column(Integer, default=15)

    is_working_day = Column(Boolean, default=True)
    is_holiday = Column(Boolean, default=False)
    is_vacation = Column(Boolean, default=False)
    notes = Column(Text)
    scheduled_tasks = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="daily_schedules")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete='CASCADE'), nullable=True)
    
    title = Column(String(200), nullable=False)
    message = Column(Text)
    type = Column(String(50))
    priority = Column(String(20), default="normal")
    
    scheduled_time = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")
    task = relationship("Task", back_populates="notifications")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE'), unique=True)

    theme = Column(String(20), default="light")
    accent_color = Column(String(7), default="#667eea")
    
    reminder_time = Column(Integer, default=30)
    daily_report_time = Column(Time, default="18:00:00")
    weekly_report_day = Column(Integer, default=6)

    default_work_hours = Column(Float, default=8.0)
    default_break_hours = Column(Float, default=1.0)
    work_days = Column(String(20), default="1,2,3,4,5")

    show_productivity_stats = Column(Boolean, default=True)
    show_time_breakdown = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    
    token = Column(String(255), unique=True, index=True)
    device_info = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    login_time = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="sessions")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    
    date = Column(DateTime, nullable=False, index=True)

    tasks_completed = Column(Integer, default=0)
    tasks_created = Column(Integer, default=0)
    total_time_spent = Column(Float, default=0.0)
    estimated_time = Column(Float, default=0.0)
    productivity_score = Column(Float, default=0.0)
    
    category_time = Column(Text)
    priority_distribution = Column(Text)
    
    estimated_vs_actual = Column(Float, default=0.0)
    on_time_completion_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")