# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import List, Optional
from app import models, schemas, crud
from app.database import get_db
import os
import re

router = APIRouter(prefix="/auth", tags=["auth"])

# Настройка хэширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=True)

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ===== Вспомогательные функции =====

def create_access_token(data: dict):
    """Создание JWT-токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хэширование пароля"""
    return pwd_context.hash(password)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """Получение текущего пользователя по JWT-токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    # Проверяем, активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user

# ===== 1. Регистрация =====
@router.post("/register", response_model=schemas.UserResponse)
def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Регистрация нового пользователя.
    """
    # Проверка email на уникальность
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Проверка username на уникальность
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Создаем пользователя
    return crud.create_user(db=db, user=user)

# ===== 2. Вход (получение токена) =====
@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Вход в систему. Возвращает JWT-токен.
    - **username**: email пользователя
    - **password**: пароль
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ===== 3. Получение информации о текущем пользователе =====


@router.get("/me", response_model=schemas.UserResponse)
def get_me(
    current_user: models.User = Depends(get_current_user)
):
    """
    Получить информацию о текущем пользователе.
    Требуется аутентификация.
    """
    return current_user

# ===== 4. Получение списка пользователей =====


@router.get("/users", response_model=schemas.UserListResponse)
def get_users(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(
        10, ge=1, le=100, description="Максимальное количество записей"),
    search: Optional[str] = Query(
        None, description="Поиск по username или email"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Получить список всех пользователей (только для авторизованных пользователей).
    Поддерживает пагинацию и поиск.
    """
    query = db.query(models.User)

    # Поиск по username или email
    if search:
        query = query.filter(
            (models.User.username.ilike(f"%{search}%")) |
            (models.User.email.ilike(f"%{search}%"))
        )

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    return schemas.UserListResponse(
        users=[schemas.UserResponse.from_orm(u) for u in users],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )

# ===== 5. Смена пароля =====


@router.put("/change-password")
def change_password(
    password_data: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Смена пароля текущего пользователя.
    Требуется ввод старого и нового пароля.
    """
    # Проверяем, что новый пароль и подтверждение совпадают
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirmation do not match"
        )

    # Проверяем, что новый пароль отличается от старого
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from old password"
        )

    # Проверяем старый пароль
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Old password is incorrect"
        )

    # Обновляем пароль
    current_user.hashed_password = get_password_hash(
        password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": 200,
        "message": "Password changed successfully"
    }

# ===== 6. Сброс пароля (если забыли) =====


@router.post("/reset-password")
def reset_password(
    reset_data: schemas.PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Сброс пароля по email (упрощенная версия).
    В реальном проекте здесь должна быть отправка email с ссылкой.
    """
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirmation do not match"
        )

    user = crud.get_user_by_email(db, email=reset_data.email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User with this email not found"
        )

    # Обновляем пароль
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": 200,
        "message": f"Password reset successfully for {reset_data.email}"
    }

# ===== 7. Обновление профиля =====


@router.put("/profile", response_model=schemas.UserResponse)
def update_profile(
    profile_data: schemas.UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Обновление профиля пользователя.
    """
    # Проверяем username на уникальность (если меняется)
    if profile_data.username and profile_data.username != current_user.username:
        existing_user = crud.get_user_by_username(
            db, username=profile_data.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        current_user.username = profile_data.username

    # Проверяем email на уникальность (если меняется)
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = crud.get_user_by_email(db, email=profile_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        current_user.email = profile_data.email

    # Обновляем полное имя
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user

# ===== 8. Деактивация аккаунта =====


@router.delete("/deactivate")
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Деактивация аккаунта (мягкое удаление).
    Пользователь не удаляется, но теряет доступ.
    """
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": 200,
        "message": "Account deactivated successfully"
    }

# ===== 9. Активация аккаунта (административная функция) =====


@router.put("/activate/{user_id}")
def activate_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Активация аккаунта пользователя.
    Только для администраторов (в реальном проекте нужна проверка прав).
    """
    # В реальном проекте проверяйте права администратора
    # if not current_user.is_admin: raise HTTPException(...)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "status": 200,
        "message": f"User {user.username} activated successfully"
    }
