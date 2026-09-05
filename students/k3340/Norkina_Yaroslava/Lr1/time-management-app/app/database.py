# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pathlib import Path
from typing import Generator

# Загружаем .env
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Получаем параметры
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Кодируем пароль для безопасной передачи в URL
encoded_password = quote_plus(DB_PASSWORD)

# Формируем строку подключения
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Выводим безопасную версию для отладки (без пароля)
safe_url = DATABASE_URL
if '@' in DATABASE_URL:
    parts = DATABASE_URL.split('@')
    if '://' in parts[0]:
        user_pass = parts[0].split('://')[1]
        safe_url = DATABASE_URL.replace(
            user_pass, f"{user_pass.split(':')[0]}:****")
print(f"Подключение к БД: {safe_url}")

# Создаем движок
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """Генератор сессий для FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)
