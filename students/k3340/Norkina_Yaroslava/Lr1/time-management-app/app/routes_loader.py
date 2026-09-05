# app/routes_loader.py
"""
Загрузчик маршрутов для избежания циклических импортов.
"""
def load_routes():
    from app.routes import auth, tasks, time_entries, analytics, categories, tags, schedules
    return {
        "auth": auth,
        "tasks": tasks,
        "time_entries": time_entries,
        "analytics": analytics,
        "categories": categories,
        "tags": tags,
        "schedules": schedules
    }