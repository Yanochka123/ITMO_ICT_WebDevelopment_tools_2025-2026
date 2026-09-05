# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import TaskStatus, PriorityLevel, RecurrenceType

# ===== User Schemas =====
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    is_premium: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ===== Category Schemas =====
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=50)
    color: str = Field(default="#667eea", max_length=7)
    icon: Optional[str] = None
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    task_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

# ===== Tag Schemas =====
class TagBase(BaseModel):
    name: str = Field(..., max_length=30)
    color: str = Field(default="#6c757d", max_length=7)

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=30)
    color: Optional[str] = Field(None, max_length=7)

class TagResponse(TagBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== Task Schemas =====
class TaskBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: PriorityLevel = PriorityLevel.MEDIUM
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_time: float = Field(default=0.0, ge=0)
    is_recurring: bool = False
    recurrence_rule: RecurrenceType = RecurrenceType.NONE
    is_favorite: bool = False
    category_id: Optional[int] = None
    parent_task_id: Optional[int] = None

class TaskCreate(TaskBase):
    tag_ids: Optional[List[int]] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[PriorityLevel] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_time: Optional[float] = Field(None, ge=0)
    progress: Optional[float] = Field(None, ge=0, le=100)
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[RecurrenceType] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    category_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

class TaskResponse(TaskBase):
    id: int
    priority_score: int
    progress: float
    time_spent: float
    time_allocated: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    is_archived: bool
    order_index: int
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    subtasks: List["TaskResponse"] = []
    time_entries: List["TimeEntryResponse"] = []
    
    class Config:
        from_attributes = True

# ===== TimeEntry Schemas =====
class TimeEntryBase(BaseModel):
    task_id: int
    description: Optional[str] = None
    start_time: Optional[datetime] = None

class TimeEntryCreate(TimeEntryBase):
    pass

class TimeEntryUpdate(BaseModel):
    description: Optional[str] = None
    end_time: Optional[datetime] = None

class TimeEntryResponse(TimeEntryBase):
    id: int
    end_time: Optional[datetime] = None
    duration: float
    is_running: bool
    created_at: datetime
    task: Optional[TaskResponse] = None
    
    class Config:
        from_attributes = True

# ===== DailySchedule Schemas =====
class DailyScheduleBase(BaseModel):
    date: datetime
    work_start: Optional[str] = "09:00:00"
    work_end: Optional[str] = "18:00:00"
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    break_duration: int = 15
    is_working_day: bool = True
    notes: Optional[str] = None
    scheduled_tasks: Optional[List[int]] = []

class DailyScheduleCreate(DailyScheduleBase):
    pass

class DailyScheduleUpdate(BaseModel):
    work_start: Optional[str] = None
    work_end: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    break_duration: Optional[int] = None
    is_working_day: Optional[bool] = None
    is_holiday: Optional[bool] = None
    is_vacation: Optional[bool] = None
    notes: Optional[str] = None
    scheduled_tasks: Optional[List[int]] = None

class DailyScheduleResponse(DailyScheduleBase):
    id: int
    day_of_week: int
    is_holiday: bool
    is_vacation: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ===== Notification Schemas =====
class NotificationBase(BaseModel):
    task_id: Optional[int] = None
    title: str = Field(..., max_length=200)
    message: str
    type: str = Field(..., max_length=50)
    scheduled_time: datetime

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_sent: Optional[bool] = None

class NotificationResponse(NotificationBase):
    id: int
    priority: str
    is_sent: bool
    is_read: bool
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    task: Optional[TaskResponse] = None
    
    class Config:
        from_attributes = True

# ===== Analytics Schemas =====
class AnalyticsResponse(BaseModel):
    date: datetime
    tasks_completed: int
    tasks_created: int
    total_time_spent: float
    estimated_time: float
    productivity_score: float
    category_time: dict
    priority_distribution: dict
    estimated_vs_actual: float
    on_time_completion_rate: float

class DailySummaryResponse(BaseModel):
    total_time: float
    by_task: List[dict]
    entry_count: int

class WeeklySummaryResponse(BaseModel):
    period: str
    tasks: dict[str, int]
    total_time: float
    productivity: float
    tasks_created: int
    tasks_completed: int

class CategoryBreakdownResponse(BaseModel):
    categories: List[dict]
    total_time: float

class TaskStatisticsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float
    total_time_spent: float
    tasks_by_priority: dict[str, int]

# ===== Statistics Schemas =====
class TaskStatistics(BaseModel):
    total_tasks: int
    by_status: dict
    by_priority: dict
    overdue_count: int
    due_today_count: int
    completion_rate: float
    total_time_spent: float
    total_estimated_time: float

class TimeSummary(BaseModel):
    total_time: float
    by_task: List[dict]
    entry_count: int

# ===== RecurringTask Schemas =====
class RecurringTaskBase(BaseModel):
    task_id: int
    recurrence_type: RecurrenceType
    interval: int = 1
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None

class RecurringTaskCreate(RecurringTaskBase):
    pass

class RecurringTaskResponse(RecurringTaskBase):
    id: int
    current_occurrence: int
    last_generated: Optional[datetime] = None
    next_generation: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ===== Delete Response =====
class DeleteResponse(BaseModel):
    status: int
    message: str


class TaskDetailResponse(TaskResponse):
    """Расширенный ответ с деталями аналитики по задаче"""
    total_time_spent: float = 0.0
    estimated_vs_actual: float = 0.0
    time_by_day: Optional[List[Dict]] = []
    avg_session_time: float = 0.0
    total_sessions: int = 0
    efficiency_score: float = 0.0
    
    class Config:
        from_attributes = True

# Обновляем forward references
TaskResponse.model_rebuild()
TaskDetailResponse.model_rebuild()