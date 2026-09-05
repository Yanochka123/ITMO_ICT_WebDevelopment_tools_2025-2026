import os
from urllib.parse import quote_plus
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

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
db_url = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"🔗 Подключение к БД: postgresql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}")


# ============================================================
# 1. ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ============================================================

# Указываем путь к файлу .env (находится в той же папке)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ============================================================
# 2. ПОЛУЧЕНИЕ ПАРАМЕТРОВ ПОДКЛЮЧЕНИЯ
# ============================================================

# Получаем параметры из .env или используем значения по умолчанию
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "bd")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "135papin")

# ============================================================
# 3. ПРОВЕРКА НАЛИЧИЯ ПАРОЛЯ
# ============================================================

if not DB_PASSWORD:
    print("⚠️ ВНИМАНИЕ: Пароль не загружен из .env файла!")
    print(f"   Текущая директория: {os.getcwd()}")
    print(f"   Путь к .env: {env_path.absolute()}")
    print("   Убедитесь, что в файле .env есть строка: DB_PASSWORD=ваш_пароль")

# ============================================================
# 4. ФОРМИРОВАНИЕ СТРОКИ ПОДКЛЮЧЕНИЯ
# ============================================================

# Собираем URL для подключения к PostgreSQL
db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Выводим безопасную версию для отладки (без пароля)
safe_url = db_url
if '@' in db_url:
    # Скрываем пароль в выводе
    parts = db_url.split('@')
    user_pass = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
    safe_url = db_url.replace(user_pass, f"{user_pass.split(':')[0]}:****")
    
print(f"🔗 Подключение к БД: {safe_url}")

# ============================================================
# 5. СОЗДАНИЕ ДВИЖКА (ENGINE)
# ============================================================

# create_engine - создает соединение с БД
# echo=True - выводит все SQL-запросы в консоль (полезно для отладки)
engine = create_engine(db_url, echo=True)

# ============================================================
# 6. ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ СЕССИИ
# ============================================================

def get_session():
    """
    Генератор сессий для работы с БД.
    Используется в эндпоинтах через Depends(get_session)
    
    Пример использования:
    @app.get("/users")
    def get_users(session: Session = Depends(get_session)):
        return session.exec(select(User)).all()
    """
    with Session(engine) as session:
        yield session

# ============================================================
# 7. (ОПЦИОНАЛЬНО) ФУНКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ ПОДКЛЮЧЕНИЯ
# ============================================================

def test_connection():
    """
    Тестовая функция для проверки подключения к БД.
    Можно запустить отдельно: python database.py
    """
    try:
        with Session(engine) as session:
            # Выполняем простой запрос для проверки
            result = session.exec("SELECT 1").all()
            print("✅ Подключение к базе данных успешно!")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

# ============================================================
# 8. ЗАПУСК ТЕСТА ПРИ НЕПОСРЕДСТВЕННОМ ВЫПОЛНЕНИИ ФАЙЛА
# ============================================================

if __name__ == "__main__":
    # Этот код выполнится только если запустить файл напрямую:
    # python database.py
    test_connection()