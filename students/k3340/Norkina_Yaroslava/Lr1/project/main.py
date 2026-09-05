from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from model import User, Category, Product

app = FastAPI()

@app.on_event("startup")
def on_startup():
    """Выполняется при запуске приложения"""
    print("🚀 Запуск приложения...")
    
    # ⚠️ ВРЕМЕННО: удаляем старые таблицы и создаем новые
    # УДАЛИТЕ ЭТИ СТРОКИ ПОСЛЕ ПЕРВОГО УСПЕШНОГО ЗАПУСКА!
    print("⚠️ Пересоздание таблиц (все данные будут удалены)...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("✅ Таблицы пересозданы с обновленной структурой")
    
    # Создаем тестовые данные
    with Session(engine) as session:
        # Проверяем и создаем категории
        existing_categories = session.exec(select(Category)).first()
        if existing_categories is None:
            categories = [
                Category(name="Электроника", description="Телефоны, ноутбуки, планшеты"),
                Category(name="Одежда", description="Мужская и женская одежда"),
                Category(name="Книги", description="Художественная и техническая литература")
            ]
            session.add_all(categories)
            session.commit()
            print("✅ Созданы тестовые категории")
        
        # Проверяем и создаем пользователей
        existing_users = session.exec(select(User)).first()
        if existing_users is None:
            users = [
                User(name="Иван", email="ivan@example.com", age=25),
                User(name="Алексей", email="alex@example.com", age=30),
                User(name="Мария", email="maria@example.com", age=28)
            ]
            session.add_all(users)
            session.commit()
            print("✅ Созданы тестовые пользователи")
        
        # Проверяем и создаем товары
        existing_products = session.exec(select(Product)).first()
        if existing_products is None:
            # Получаем первую категорию для связи
            category = session.exec(select(Category)).first()
            if category:
                products = [
                    Product(name="Ноутбук", price=1500.00, category_id=category.id),
                    Product(name="Смартфон", price=800.00, category_id=category.id),
                    Product(name="Наушники", price=150.00, category_id=category.id)
                ]
                session.add_all(products)
                session.commit()
                print("✅ Созданы тестовые товары")
    
    print("✅ Приложение готово к работе!")

@app.get("/")
def hello():
    return {"message": "Hello, User! 👋"}

@app.get("/users")
def get_users(session: Session = Depends(get_session)):
    """Получить всех пользователей"""
    users = session.exec(select(User)).all()
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_session)):
    """Получить пользователя по ID"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users")
def create_user(user: User, session: Session = Depends(get_session)):
    """Создать нового пользователя"""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/categories")
def get_categories(session: Session = Depends(get_session)):
    """Получить все категории"""
    categories = session.exec(select(Category)).all()
    return categories

@app.post("/categories")
def create_category(category: Category, session: Session = Depends(get_session)):
    """Создать новую категорию"""
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@app.get("/products")
def get_products(session: Session = Depends(get_session)):
    """Получить все товары"""
    products = session.exec(select(Product)).all()
    return products

@app.post("/products")
def create_product(product: Product, session: Session = Depends(get_session)):
    """Создать новый товар"""
    session.add(product)
    session.commit()
    session.refresh(product)
    return product