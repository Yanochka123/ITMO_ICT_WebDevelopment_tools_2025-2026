import os
import sys
import time
import random
import asyncio
from pathlib import Path
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent           # .../time-management-app/Task_2/
PROJECT_ROOT = CURRENT_DIR.parent  

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "time_management_db")

SYNC_DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


from sqlalchemy import create_engine, delete, func, select as sa_select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession


from app.models import (
    User,
    Task,
    Category,
    Tag,
    task_tags,
)
from app.models import PriorityLevel, TaskStatus

# Подключение к БД

sync_engine = create_engine(SYNC_DB_URL)
async_engine = create_async_engine(ASYNC_DB_URL)
async_session_factory = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Константы нового пользователя


PARSER_USERNAME = "parser"
PARSER_EMAIL = "parser@local"
PARSER_FULL_NAME = "Technical Parser User"
PARSER_DEFAULT_COLOR = "#6c757d"
PARSER_DEFAULT_TAG_COLOR = "#6c757d"

PRIORITY_MAP = {
    "low": PriorityLevel.LOW,
    "medium": PriorityLevel.MEDIUM,
    "high": PriorityLevel.HIGH,
    "urgent": PriorityLevel.URGENT,
    "critical": PriorityLevel.CRITICAL,
}


# Синхронные функции созданния парсера

def _get_or_create_parser_user_sync(session: Session) -> User:
    # Возвращает/создаёт технического пользователя 'parser'
    user = session.exec(
        select(User).where(User.username == PARSER_USERNAME)
    ).first()
    if user:
        return user

    # hashed_password NOT NULL — кладём sha256 от случайной строки
    import hashlib
    fake_password = hashlib.sha256(os.urandom(32)).hexdigest()

    user = User(
        username=PARSER_USERNAME,
        email=PARSER_EMAIL,
        hashed_password=fake_password,
        full_name=PARSER_FULL_NAME,
        timezone="UTC",
        is_active=True,
        is_premium=False,
        email_notifications=False,
        push_notifications=False,
    )
    session.add(user)
    session.flush()
    return user


def _get_or_create_category_sync(session: Session, name: str, user_id: int) -> Category:
    # Возвращает/создаёт категорию по имени для пользователя
    category = session.exec(
        select(Category).where(
            func.lower(Category.name) == name.lower(),
            Category.user_id == user_id,
        )
    ).first()
    if category:
        return category

    category = Category(
        name=name[:50],
        color=PARSER_DEFAULT_COLOR,
        icon="📥",
        description=f"Импортировано парсером",
        user_id=user_id,
    )
    session.add(category)
    session.flush()
    return category


def _get_or_create_tag_sync(session: Session, name: str, user_id: int) -> Tag:
    """Возвращает/создаёт тег по имени для пользователя."""
    tag = session.exec(
        select(Tag).where(
            func.lower(Tag.name) == name.lower(),
            Tag.user_id == user_id,
        )
    ).first()
    if tag:
        return tag

    tag = Tag(
        name=name[:100],
        color=PARSER_DEFAULT_TAG_COLOR,
        user_id=user_id,
    )
    session.add(tag)
    session.flush()
    return tag



def save_to_db_sync(page_data: dict, retries: int = 3):
    """
    Синхронная функция сохранения страниц в базу данных тайм-менеджера    
    page_data — результат extract_page_info():
        {
            "external_id": str,
            "title": str,
            "description": str,
            "language": str,
            "keywords": list[str],
            "estimated_hours": float,
            "priority": str,
            "category_hint": str,
            "url": str,
        }
    
    Создаёт:
        - Task (title, description, priority, estimated_time, user_id=parser)
        - Category (по category_hint)
        - Tag для каждого keyword
        - Связи task_tags
    """
    for attempt in range(retries):
        try:
            with Session(sync_engine) as session:
                # 1. Проверка на дубликат по title
                existing = session.exec(
                    select(Task).where(
                        func.lower(Task.title) == page_data["title"].lower()
                    )
                ).first()
                if existing:
                    return

                # 2. Пользователь
                parser_user = _get_or_create_parser_user_sync(session)

                # 3. Категория
                category = _get_or_create_category_sync(
                    session,
                    page_data.get("category_hint", "Прочее"),
                    parser_user.id,
                )

                # 4. Задача
                task = Task(
                    title=page_data["title"][:200],
                    description=page_data["description"],
                    status=TaskStatus.PENDING,
                    priority=PRIORITY_MAP.get(
                        page_data.get("priority", "medium"),
                        PriorityLevel.MEDIUM,
                    ),
                    estimated_time=page_data.get("estimated_hours", 1.0),
                    user_id=parser_user.id,
                    category_id=category.id,
                    is_archived=False,
                    is_favorite=False,
                )
                session.add(task)
                session.flush()

                # 5. Теги из keywords
                for keyword in page_data.get("keywords", []):
                    tag = _get_or_create_tag_sync(
                        session, keyword, parser_user.id
                    )
                    # Привязка через task_tags (many-to-many)
                    session.execute(
                        task_tags.insert().values(
                            task_id=task.id,
                            tag_id=tag.id,
                        )
                    )

                session.commit()
                return
        except IntegrityError:
            # Race condition: два процесса одновременно создают один и тот же тег/категорию
            if attempt < retries - 1:
                time.sleep(random.uniform(0.1, 0.4))
                continue
            else:
                raise
        except Exception as e:
            raise e


# Асинхронные функции

async def _get_or_create_parser_user_async(session: AsyncSession) -> User:
    result = await session.exec(
        select(User).where(User.username == PARSER_USERNAME)
    )
    user = result.first()
    if user:
        return user

    import hashlib
    fake_password = hashlib.sha256(os.urandom(32)).hexdigest()

    user = User(
        username=PARSER_USERNAME,
        email=PARSER_EMAIL,
        hashed_password=fake_password,
        full_name=PARSER_FULL_NAME,
        timezone="UTC",
        is_active=True,
        is_premium=False,
        email_notifications=False,
        push_notifications=False,
    )
    session.add(user)
    await session.flush()
    return user


async def _get_or_create_category_async(
    session: AsyncSession, name: str, user_id: int
) -> Category:
    result = await session.exec(
        select(Category).where(
            func.lower(Category.name) == name.lower(),
            Category.user_id == user_id,
        )
    )
    category = result.first()
    if category:
        return category

    category = Category(
        name=name[:50],
        color=PARSER_DEFAULT_COLOR,
        icon="📥",
        description="Импортировано парсером",
        user_id=user_id,
    )
    session.add(category)
    await session.flush()
    return category


async def _get_or_create_tag_async(
    session: AsyncSession, name: str, user_id: int
) -> Tag:
    result = await session.exec(
        select(Tag).where(
            func.lower(Tag.name) == name.lower(),
            Tag.user_id == user_id,
        )
    )
    tag = result.first()
    if tag:
        return tag

    tag = Tag(
        name=name[:100],
        color=PARSER_DEFAULT_TAG_COLOR,
        user_id=user_id,
    )
    session.add(tag)
    await session.flush()
    return tag

# Асинхронное сохранение

async def save_to_db_async(page_data: dict, retries: int = 3):
    """
    Асинхронная версия save_to_db_sync.
    Использует asyncpg + AsyncSession.
    """
    for attempt in range(retries):
        try:
            async with async_session_factory() as session:
                # 1. Дубликат по title
                result = await session.exec(
                    select(Task).where(
                        func.lower(Task.title) == page_data["title"].lower()
                    )
                )
                if result.first():
                    return

                # 2. Технический пользователь
                parser_user = await _get_or_create_parser_user_async(session)

                # 3. Категория
                category = await _get_or_create_category_async(
                    session,
                    page_data.get("category_hint", "Прочее"),
                    parser_user.id,
                )

                # 4. Задача
                task = Task(
                    title=page_data["title"][:200],
                    description=page_data["description"],
                    status=TaskStatus.PENDING,
                    priority=PRIORITY_MAP.get(
                        page_data.get("priority", "medium"),
                        PriorityLevel.MEDIUM,
                    ),
                    estimated_time=page_data.get("estimated_hours", 1.0),
                    user_id=parser_user.id,
                    category_id=category.id,
                    is_archived=False,
                    is_favorite=False,
                )
                session.add(task)
                await session.flush()

                # 5. Теги
                for keyword in page_data.get("keywords", []):
                    tag = await _get_or_create_tag_async(
                        session, keyword, parser_user.id
                    )
                    await session.execute(
                        task_tags.insert().values(
                            task_id=task.id,
                            tag_id=tag.id,
                        )
                    )

                await session.commit()
                return
        except IntegrityError:
            if attempt < retries - 1:
                await asyncio.sleep(random.uniform(0.1, 0.4))
                continue
            else:
                raise
        except Exception as e:
            raise e



def clean_db_sync():
    """
    Полностью очищает задачи, теги, категории и связи,
    созданные пользователем 'parser'
    """
    try:
        with Session(sync_engine) as session:
            # 1. Находим пользователя parser
            parser_user = session.exec(
                select(User).where(User.username == PARSER_USERNAME)
            ).first()
            if not parser_user:
                print("[Очистка] Пользователь 'parser' не найден — нечего чистить.")
                return

            # 2. Удаляем связи task_tags для задач parser'а
            task_ids_subq = sa_select(Task.id).where(
                Task.user_id == parser_user.id
            )
            session.execute(
                task_tags.delete().where(task_tags.c.task_id.in_(task_ids_subq))
            )

            # 3. Удаляем задачи parser'а
            session.execute(
                delete(Task).where(Task.user_id == parser_user.id)
            )

            # 4. Удаляем теги parser'а
            session.execute(
                delete(Tag).where(Tag.user_id == parser_user.id)
            )

            # 5. Удаляем категории parser'а
            session.execute(
                delete(Category).where(Category.user_id == parser_user.id)
            )

            session.commit()
            print("[Очистка] Все данные парсера удалены.")
    except Exception as e:
        print(f"[БД Ошибка] Не удалось очистить базу: {e}")
        raise e