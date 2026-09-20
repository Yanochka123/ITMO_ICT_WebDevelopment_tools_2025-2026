# main.py
from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from schemas import (
    Task, TaskCreate, TaskUpdate, TaskStatusEnum, PriorityEnum,
    Category, Tag, Subtask, TimeEntry,
    CategoryCreate, TagCreate, SubtaskCreate, TimeEntryCreate,
    DeleteResponse
)

app = FastAPI(
    title="Time Management API",
    description="API для управления задачами и временем",
    version="1.0.0"
)

# ==================== ВРЕМЕННАЯ БАЗА ДАННЫХ ====================
temp_bd: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Разработка дизайна для веб-приложения",
        "description": "Создать макеты главной страницы и личного кабинета в Figma",
        "status": "in_progress",
        "priority": "high",
        "deadline": "2026-08-10T18:00:00",  # Обновлено для тестирования
        "estimated_time": 240,
        "created_at": "2026-07-13T09:00:00",
        "updated_at": "2026-07-13T09:00:00",
        "completed_at": None,
        "category": {
            "id": 1,
            "name": "Дизайн",
            "description": "Задачи по дизайну интерфейсов",
            "color": "#FF6B6B"
        },
        "tags": [
            {"id": 1, "name": "Дизайн", "color": "#FF6B6B"},
            {"id": 2, "name": "Figma", "color": "#A8E6CF"}
        ],
        "subtasks": [
            {"id": 1, "title": "Создать структуру страниц", "is_completed": True, "created_at": "2026-07-13T09:30:00"},
            {"id": 2, "title": "Разработать главный экран", "is_completed": False, "created_at": "2026-07-13T10:00:00"},
            {"id": 3, "title": "Разработать личный кабинет", "is_completed": False, "created_at": "2026-07-13T10:30:00"}
        ],
        "time_entries": [
            {"id": 1, "start_time": "2026-07-13T09:00:00", "end_time": "2026-07-13T11:00:00", "duration_minutes": 120, "description": "Создание структуры"},
            {"id": 2, "start_time": "2026-07-13T12:00:00", "end_time": "2026-07-13T14:00:00", "duration_minutes": 120, "description": "Разработка главного экрана"}
        ],
        "is_recurring": False,
        "recurring_rule": None
    },
    {
        "id": 2,
        "title": "Написание документации к проекту",
        "description": "Описать архитектуру, API и инструкцию по развертыванию",
        "status": "pending",
        "priority": "medium",
        "deadline": "2026-08-15T23:59:00",  # Обновлено для тестирования
        "estimated_time": 180,
        "created_at": "2026-07-12T14:00:00",
        "updated_at": "2026-07-12T14:00:00",
        "completed_at": None,
        "category": {
            "id": 2,
            "name": "Документация",
            "description": "Создание и поддержка документации",
            "color": "#4ECDC4"
        },
        "tags": [
            {"id": 3, "name": "Документация", "color": "#4ECDC4"},
            {"id": 4, "name": "Техническое", "color": "#95A5A6"}
        ],
        "subtasks": [
            {"id": 4, "title": "Описать архитектуру", "is_completed": False, "created_at": "2026-07-12T14:30:00"},
            {"id": 5, "title": "Описать API", "is_completed": False, "created_at": "2026-07-12T15:00:00"},
            {"id": 6, "title": "Написать инструкцию", "is_completed": False, "created_at": "2026-07-12T15:30:00"}
        ],
        "time_entries": [
            {"id": 3, "start_time": "2026-07-12T14:00:00", "end_time": "2026-07-12T15:30:00", "duration_minutes": 90, "description": "Начало документации"}
        ],
        "is_recurring": False,
        "recurring_rule": None
    },
    {
        "id": 3,
        "title": "Еженедельная встреча команды",
        "description": "Обсуждение текущих задач и планирование на следующую неделю",
        "status": "completed",
        "priority": "urgent",
        "deadline": "2026-07-13T11:00:00",
        "estimated_time": 60,
        "created_at": "2026-07-10T10:00:00",
        "updated_at": "2026-07-13T11:30:00",
        "completed_at": "2026-07-13T11:00:00",
        "category": {
            "id": 3,
            "name": "Совещания",
            "description": "Плановые и внеплановые встречи",
            "color": "#FFD93D"
        },
        "tags": [
            {"id": 5, "name": "Команда", "color": "#FFD93D"},
            {"id": 6, "name": "Еженедельное", "color": "#6C5B7B"}
        ],
        "subtasks": [
            {"id": 7, "title": "Подготовить отчет", "is_completed": True, "created_at": "2026-07-12T09:00:00"},
            {"id": 8, "title": "Провести встречу", "is_completed": True, "created_at": "2026-07-13T10:30:00"}
        ],
        "time_entries": [
            {"id": 4, "start_time": "2026-07-13T10:00:00", "end_time": "2026-07-13T11:00:00", "duration_minutes": 60, "description": "Еженедельная встреча"}
        ],
        "is_recurring": True,
        "recurring_rule": "weekly"
    }
]

# ==================== ВСПОМОГАТЕЛЬНЫЕ БАЗЫ ДАННЫХ ====================
categories_bd = [
    {"id": 1, "name": "Дизайн", "description": "Задачи по дизайну интерфейсов", "color": "#FF6B6B"},
    {"id": 2, "name": "Документация", "description": "Создание и поддержка документации", "color": "#4ECDC4"},
    {"id": 3, "name": "Совещания", "description": "Плановые и внеплановые встречи", "color": "#FFD93D"},
    {"id": 4, "name": "Разработка", "description": "Программирование и разработка", "color": "#A8E6CF"}
]

tags_bd = [
    {"id": 1, "name": "Дизайн", "color": "#FF6B6B"},
    {"id": 2, "name": "Figma", "color": "#A8E6CF"},
    {"id": 3, "name": "Документация", "color": "#4ECDC4"},
    {"id": 4, "name": "Техническое", "color": "#95A5A6"},
    {"id": 5, "name": "Команда", "color": "#FFD93D"},
    {"id": 6, "name": "Еженедельное", "color": "#6C5B7B"},
    {"id": 7, "name": "Бэкенд", "color": "#FF8C94"},
    {"id": 8, "name": "Фронтенд", "color": "#87CEEB"}
]

# Счетчики
task_id_counter = 4
category_id_counter = 5
tag_id_counter = 9
subtask_id_counter = 9
time_entry_id_counter = 5

# ==================== ЭНДПОИНТЫ ====================

# GET: Получить все задачи
@app.get("/api/tasks", response_model=List[Task])
def get_all_tasks() -> List[Dict[str, Any]]:
    """Получить список всех задач с вложенными объектами"""
    return temp_bd

# GET: Получить задачи с приближающимся дедлайном
@app.get("/api/tasks/deadlines/upcoming", response_model=List[Task])
def get_tasks_with_upcoming_deadlines(
    hours: int = Query(24, description="Количество часов до дедлайна")
) -> List[Dict[str, Any]]:
    """Получить задачи, у которых дедлайн наступает в ближайшие N часов"""
    now = datetime.now()
    deadline_threshold = now + timedelta(hours=hours)
    
    result = []
    for task in temp_bd:
        if task["deadline"] and task["status"] != "completed":
            try:
                deadline = datetime.fromisoformat(task["deadline"])
                if now <= deadline <= deadline_threshold:
                    result.append(task)
            except (ValueError, TypeError):
                continue
    return result

# GET: Статистика по задачам
@app.get("/api/tasks/statistics")
def get_task_statistics() -> Dict[str, Any]:
    """Получить статистику по задачам"""
    total = len(temp_bd)
    completed = len([t for t in temp_bd if t["status"] == "completed"])
    in_progress = len([t for t in temp_bd if t["status"] == "in_progress"])
    pending = len([t for t in temp_bd if t["status"] == "pending"])
    
    total_time = 0
    for task in temp_bd:
        for entry in task["time_entries"]:
            if entry.get("duration_minutes"):
                total_time += entry["duration_minutes"]
    
    by_priority = {}
    for priority in [p.value for p in PriorityEnum]:
        by_priority[priority] = len([t for t in temp_bd if t["priority"] == priority])
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "pending_tasks": pending,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 2),
        "total_time_spent_minutes": total_time,
        "tasks_by_priority": by_priority
    }

# GET: Получить задачи по статусу
@app.get("/api/tasks/status/{status}", response_model=List[Task])
def get_tasks_by_status(status: TaskStatusEnum) -> List[Dict[str, Any]]:
    """Получить задачи по статусу"""
    return [task for task in temp_bd if task["status"] == status.value]

# GET: Получить задачи по приоритету
@app.get("/api/tasks/priority/{priority}", response_model=List[Task])
def get_tasks_by_priority(priority: PriorityEnum) -> List[Dict[str, Any]]:
    """Получить задачи по приоритету"""
    return [task for task in temp_bd if task["priority"] == priority.value]

# GET: Получить задачу по ID
@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task_by_id(task_id: int) -> Dict[str, Any]:
    """Получить задачу по ID с её вложенными объектами"""
    task = next((task for task in temp_bd if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task

# POST: Создать новую задачу
@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate) -> Dict[str, Any]:
    """Создать новую задачу с вложенными объектами"""
    global task_id_counter
    
    category = None
    if task.category_id:
        category = next((cat for cat in categories_bd if cat["id"] == task.category_id), None)
    
    tags = []
    if task.tag_ids:
        tags = [tag for tag in tags_bd if tag["id"] in task.tag_ids]
    
    new_task = {
        "id": task_id_counter,
        "title": task.title,
        "description": task.description,
        "status": "pending",
        "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "estimated_time": task.estimated_time,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "completed_at": None,
        "category": category,
        "tags": tags,
        "subtasks": [],
        "time_entries": [],
        "is_recurring": task.is_recurring,
        "recurring_rule": task.recurring_rule
    }
    
    temp_bd.append(new_task)
    task_id_counter += 1
    return new_task

# PUT: Обновить задачу
@app.put("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate) -> Dict[str, Any]:
    """Обновить задачу по ID"""
    task_index = next((i for i, t in enumerate(temp_bd) if t["id"] == task_id), None)
    if task_index is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    
    task = temp_bd[task_index]
    update_data = task_update.dict(exclude_unset=True)
    
    if "title" in update_data:
        task["title"] = update_data["title"]
    if "description" in update_data:
        task["description"] = update_data["description"]
    if "status" in update_data:
        task["status"] = update_data["status"].value if hasattr(update_data["status"], 'value') else update_data["status"]
        if task["status"] == "completed":
            task["completed_at"] = datetime.now().isoformat()
    if "priority" in update_data:
        task["priority"] = update_data["priority"].value if hasattr(update_data["priority"], 'value') else update_data["priority"]
    if "deadline" in update_data:
        task["deadline"] = update_data["deadline"].isoformat() if update_data["deadline"] else None
    if "estimated_time" in update_data:
        task["estimated_time"] = update_data["estimated_time"]
    if "category_id" in update_data and update_data["category_id"] is not None:
        category = next((cat for cat in categories_bd if cat["id"] == update_data["category_id"]), None)
        task["category"] = category
    if "tag_ids" in update_data and update_data["tag_ids"] is not None:
        tags = [tag for tag in tags_bd if tag["id"] in update_data["tag_ids"]]
        task["tags"] = tags
    if "is_recurring" in update_data:
        task["is_recurring"] = update_data["is_recurring"]
    if "recurring_rule" in update_data:
        task["recurring_rule"] = update_data["recurring_rule"]
    
    task["updated_at"] = datetime.now().isoformat()
    temp_bd[task_index] = task
    
    return task

# DELETE: Удалить задачу
@app.delete("/api/tasks/{task_id}", response_model=DeleteResponse)
def delete_task(task_id: int) -> Dict[str, Any]:
    """Удалить задачу по ID"""
    task_index = next((i for i, t in enumerate(temp_bd) if t["id"] == task_id), None)
    if task_index is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    
    temp_bd.pop(task_index)
    return {"status": 200, "message": f"Task with id {task_id} deleted successfully"}


# ==================== API ДЛЯ ВЛОЖЕННЫХ ОБЪЕКТОВ ====================

# ---------- CATEGORIES ----------
@app.get("/api/categories", response_model=List[Category])
def get_all_categories() -> List[Dict[str, Any]]:
    """Получить все категории"""
    return categories_bd

@app.post("/api/categories", response_model=Category, status_code=201)
def create_category(category: CategoryCreate) -> Dict[str, Any]:
    """Создать новую категорию"""
    global category_id_counter
    new_category = {
        "id": category_id_counter,
        "name": category.name,
        "description": category.description,
        "color": category.color
    }
    categories_bd.append(new_category)
    category_id_counter += 1
    return new_category

@app.delete("/api/categories/{category_id}", response_model=DeleteResponse)
def delete_category(category_id: int) -> Dict[str, Any]:
    """Удалить категорию"""
    category_index = next((i for i, c in enumerate(categories_bd) if c["id"] == category_id), None)
    if category_index is None:
        raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
    categories_bd.pop(category_index)
    return {"status": 200, "message": f"Category with id {category_id} deleted successfully"}

# ---------- TAGS ----------
@app.get("/api/tags", response_model=List[Tag])
def get_all_tags() -> List[Dict[str, Any]]:
    """Получить все теги"""
    return tags_bd

@app.post("/api/tags", response_model=Tag, status_code=201)
def create_tag(tag: TagCreate) -> Dict[str, Any]:
    """Создать новый тег"""
    global tag_id_counter
    new_tag = {
        "id": tag_id_counter,
        "name": tag.name,
        "color": tag.color
    }
    tags_bd.append(new_tag)
    tag_id_counter += 1
    return new_tag

@app.delete("/api/tags/{tag_id}", response_model=DeleteResponse)
def delete_tag(tag_id: int) -> Dict[str, Any]:
    """Удалить тег"""
    tag_index = next((i for i, t in enumerate(tags_bd) if t["id"] == tag_id), None)
    if tag_index is None:
        raise HTTPException(status_code=404, detail=f"Tag with id {tag_id} not found")
    tags_bd.pop(tag_index)
    return {"status": 200, "message": f"Tag with id {tag_id} deleted successfully"}

# ---------- SUBTASKS ----------
@app.post("/api/tasks/{task_id}/subtasks", response_model=Subtask, status_code=201)
def add_subtask_to_task(task_id: int, subtask: SubtaskCreate) -> Dict[str, Any]:
    """Добавить подзадачу к задаче"""
    global subtask_id_counter
    
    task = next((t for t in temp_bd if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    
    new_subtask = {
        "id": subtask_id_counter,
        "title": subtask.title,
        "is_completed": subtask.is_completed,
        "created_at": datetime.now().isoformat()
    }
    task["subtasks"].append(new_subtask)
    subtask_id_counter += 1
    return new_subtask

@app.put("/api/tasks/{task_id}/subtasks/{subtask_id}", response_model=Subtask)
def update_subtask(task_id: int, subtask_id: int, subtask: SubtaskCreate) -> Dict[str, Any]:
    """Обновить подзадачу"""
    task = next((t for t in temp_bd if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    
    subtask_index = next((i for i, s in enumerate(task["subtasks"]) if s["id"] == subtask_id), None)
    if subtask_index is None:
        raise HTTPException(status_code=404, detail=f"Subtask with id {subtask_id} not found")
    
    task["subtasks"][subtask_index]["title"] = subtask.title
    task["subtasks"][subtask_index]["is_completed"] = subtask.is_completed
    return task["subtasks"][subtask_index]

@app.delete("/api/tasks/{task_id}/subtasks/{subtask_id}", response_model=DeleteResponse)
def delete_subtask(task_id: int, subtask_id: int) -> Dict[str, Any]:
    """Удалить подзадачу"""
    task = next((t for t in temp_bd if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    
    subtask_index = next((i for i, s in enumerate(task["subtasks"]) if s["id"] == subtask_id), None)
    if subtask_index is None:
        raise HTTPException(status_code=404, detail=f"Subtask with id {subtask_id} not found")
    
    task["subtasks"].pop(subtask_index)
    return {"status": 200, "message": f"Subtask with id {subtask_id} deleted successfully"}

# ---------- TIME ENTRIES ----------
@app.post("/api/tasks/{task_id}/time_entries", response_model=TimeEntry, status_code=201)
def add_time_entry_to_task(task_id: int, time_entry: TimeEntryCreate) -> Dict[str, Any]:
    """Добавить временную запись к задаче"""
    global time_entry_id_counter
    
    task = next((t for t in temp_bd if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    
    duration = None
    if time_entry.end_time:
        duration = int((time_entry.end_time - time_entry.start_time).total_seconds() / 60)
    
    new_time_entry = {
        "id": time_entry_id_counter,
        "start_time": time_entry.start_time.isoformat(),
        "end_time": time_entry.end_time.isoformat() if time_entry.end_time else None,
        "duration_minutes": duration,
        "description": time_entry.description
    }
    task["time_entries"].append(new_time_entry)
    time_entry_id_counter += 1
    return new_time_entry

@app.get("/api/tasks/{task_id}/time_entries", response_model=List[TimeEntry])
def get_task_time_entries(task_id: int) -> List[Dict[str, Any]]:
    """Получить все временные записи для задачи"""
    task = next((t for t in temp_bd if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task["time_entries"]