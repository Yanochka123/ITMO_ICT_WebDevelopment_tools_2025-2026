# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Загружаем .env
env_path = Path(__file__).parent.parent / 'app' / '.env'
load_dotenv(dotenv_path=env_path)

# Импортируем Base из database
from app.database import Base
# Импортируем все модели, чтобы Alembic их видел
from app.models import (
    User, Category, Tag, Task, RecurringTask, 
    TimeEntry, DailySchedule, Notification, 
    UserPreference, Session, Analytics
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_database_url():
    """Получение URL из переменных окружения"""
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Кодируем пароль
    encoded_password = quote_plus(DB_PASSWORD)
    
    return f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме."""
    url = get_database_url()
    
    # Создаем конфигурацию с правильным URL
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()