from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    """Модель пользователя"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=100)
    email: str = Field(unique=True, max_length=100)
    age: int = Field(ge=0, le=150)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

class Category(SQLModel, table=True):
    """Модель категории товаров"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=200)
    
    # Связь с товарами (один ко многим)
    products: List["Product"] = Relationship(back_populates="category")

class Product(SQLModel, table=True):
    """Модель товара с внешним ключом на категорию"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True)
    price: float = Field(gt=0, description="Цена товара")
    category_id: int = Field(foreign_key="category.id", description="ID категории")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Связь с категорией (многие к одному)
    category: Optional[Category] = Relationship(back_populates="products")