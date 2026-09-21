# test_db_connection.py
import sys
sys.path.append('.')

from app.database import engine, Base, DATABASE_URL
from app.models import User, Task, Category, Tag

def test_connection():
    try:
        print(f"Подключение к: {DATABASE_URL}")
        with engine.connect() as conn:
            print("✅ Подключение к БД успешно!")
            
        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы успешно!")
        
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Созданные таблицы: {tables}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()