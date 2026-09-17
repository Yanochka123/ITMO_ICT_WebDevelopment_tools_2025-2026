# app/schemas.py
from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Dict, Any, Union, List
from datetime import datetime
from app.models import *
import json

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
    is_favorite: bool = False
    category_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    recurrence_type: Optional[RecurrenceType] = None
    recurrence_rule: Optional[Union[Dict[str, Any], str, None]] = None

    @field_validator('recurrence_rule', mode='before')
    @classmethod
    def validate_recurrence_rule(cls, v):
        """Преобразует recurrence_rule в словарь или None"""
        if v is None:
            return None

        if isinstance(v, dict):
            return v

        if isinstance(v, str):
            # Если строка - это значение Enum, возвращаем None
            if v in ['none', 'daily', 'weekly', 'monthly', 'yearly']:
                return None

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None

        # Для Enum и других объектов
        return None

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
    
    # model_config = {"from_attributes": True}

    @model_validator(mode='before')
    @classmethod
    def validate_before(cls, values):
        """Преобразуем все значения перед валидацией"""
        if isinstance(values, dict):
            # Преобразуем subtasks
            if 'subtasks' in values:
                if values['subtasks'] is None:
                    values['subtasks'] = []
                elif not isinstance(values['subtasks'], list):
                    # Если это объект, а не список, превращаем в пустой список
                    values['subtasks'] = []

            # Преобразуем tags
            if 'tags' in values:
                if values['tags'] is None:
                    values['tags'] = []
                elif not isinstance(values['tags'], list):
                    values['tags'] = []

            # Преобразуем time_entries
            if 'time_entries' in values:
                if values['time_entries'] is None:
                    values['time_entries'] = []
                elif not isinstance(values['time_entries'], list):
                    values['time_entries'] = []

        return values

    @field_validator('subtasks', 'tags', 'time_entries', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Преобразуем None или объект в пустой список"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        # Если это объект (не список), возвращаем пустой список
        return []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

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
# ===== DailySchedule Schemas =====


class DailyScheduleBase(BaseModel):
    date: datetime
    work_start: Optional[time] = time(9, 0, 0)
    work_end: Optional[time] = time(18, 0, 0)
    lunch_start: Optional[time] = None
    lunch_end: Optional[time] = None
    break_duration: int = 15
    is_working_day: bool = True
    notes: Optional[str] = None
    scheduled_tasks: Optional[List[int]] = []


class DailyScheduleCreate(DailyScheduleBase):
    """Схема для создания — принимает и строки, и datetime.time"""

    @field_validator('work_start', 'work_end', 'lunch_start', 'lunch_end', mode='before')
    @classmethod
    def parse_time(cls, v):
        """Преобразует '06:00:00' в datetime.time"""
        if v is None:
            return None
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            try:
                return time.fromisoformat(v)
            except ValueError:
                raise ValueError(
                    f"Invalid time format: {v}. Expected HH:MM:SS")
        return v

    @field_validator('scheduled_tasks', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Преобразует set/tuple в list"""
        if v is None:
            return []
        if isinstance(v, (set, tuple)):
            return list(v)
        return v


class DailyScheduleUpdate(BaseModel):
    work_start: Optional[time] = None
    work_end: Optional[time] = None
    lunch_start: Optional[time] = None
    lunch_end: Optional[time] = None
    break_duration: Optional[int] = None
    is_working_day: Optional[bool] = None
    is_holiday: Optional[bool] = None
    is_vacation: Optional[bool] = None
    notes: Optional[str] = None
    scheduled_tasks: Optional[List[int]] = None

    @field_validator('work_start', 'work_end', 'lunch_start', 'lunch_end', mode='before')
    @classmethod
    def parse_time(cls, v):
        if v is None:
            return None
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            try:
                return time.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Invalid time format: {v}")
        return v

    @field_validator('scheduled_tasks', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return None
        if isinstance(v, (set, tuple)):
            return list(v)
        return v


class DailyScheduleResponse(DailyScheduleBase):
    id: int
    day_of_week: int
    is_holiday: bool
    is_vacation: bool
    created_at: datetime
    updated_at: datetime
    
    @field_validator('scheduled_tasks', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Преобразует set, tuple или PostgreSQL-строку '{16,19,20}' в list"""
        if v is None:
            return []
        if isinstance(v, (set, tuple)):
            return list(v)
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Парсим PostgreSQL-формат: '{16,19,20}'
            stripped = v.strip('{}')
            if not stripped:
                return []
            try:
                return [int(x.strip()) for x in stripped.split(',') if x.strip()]
            except ValueError:
                return []
        return v

    model_config = {"from_attributes": True}


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

# app/schemas.py (добавить в конец файла)

# ===== Password Management =====


class PasswordChange(BaseModel):
    """Схема для смены пароля"""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class PasswordReset(BaseModel):
    """Схема для сброса пароля (если забыли)"""
    email: EmailStr
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

# ===== User Management =====


class UserListResponse(BaseModel):
    """Ответ со списком пользователей"""
    users: List[UserResponse]
    total: int
    page: int
    limit: int


class UserUpdateRequest(BaseModel):
    """Схема для обновления профиля"""
    full_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class TaskCreateResponse(TaskBase):
    """Схема для ответа при создании задачи (без подзадач и временных записей)"""
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

    class Config:
        from_attributes = True
