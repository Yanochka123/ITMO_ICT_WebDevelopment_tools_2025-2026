# app/routes/__init__.py
from . import auth, tasks, time_entries, analytics, categories, tags, schedules

__all__ = [
    "auth",
    "tasks",
    "time_entries",
    "analytics",
    "categories",
    "tags",
    "schedules"
]