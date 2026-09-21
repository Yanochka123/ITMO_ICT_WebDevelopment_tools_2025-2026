# schemas.py
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# Перечисления для статусов и приоритетов
class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Модель для вложенного объекта - Категория задачи
class Category(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#808080"

# Модель для вложенного объекта - Тег задачи
class Tag(BaseModel):
    id: int
    name: str
    color: Optional[str] = "#808080"

# Модель для вложенного объекта - Подзадача
class Subtask(BaseModel):
    id: int
    title: str
    is_completed: bool = False
    created_at: Optional[datetime] = None

# Модель для вложенного объекта - Временная запись
class TimeEntry(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = 0
    description: Optional[str] = ""

# Модель для вложенного объекта - Приоритет
class Priority(BaseModel):
    id: int
    level: PriorityEnum
    label: str
    color: str

# Основная модель - Задача
class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = ""
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    priority: PriorityEnum = PriorityEnum.MEDIUM
    deadline: Optional[datetime] = None
    estimated_time: Optional[int] = None  # в минутах
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    category: Optional[Category] = None  # Одиночный вложенный объект
    tags: List[Tag] = []  # Список объектов
    subtasks: List[Subtask] = []  # Список объектов
    time_entries: List[TimeEntry] = []  # Список объектов
    is_recurring: bool = False
    recurring_rule: Optional[str] = None

# Модели для создания и обновления задач
class TaskCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = ""
    priority: PriorityEnum = PriorityEnum.MEDIUM
    deadline: Optional[datetime] = None
    estimated_time: Optional[int] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = []
    is_recurring: bool = False
    recurring_rule: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    deadline: Optional[datetime] = None
    estimated_time: Optional[int] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    is_recurring: Optional[bool] = None
    recurring_rule: Optional[str] = None

# Модели для дополнительных объектов
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#808080"

class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#808080"

class SubtaskCreate(BaseModel):
    title: str
    is_completed: bool = False

class TimeEntryCreate(BaseModel):
    task_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    description: Optional[str] = ""

# Тип ответа для удаления
class DeleteResponse(BaseModel):
    status: int
    message: str