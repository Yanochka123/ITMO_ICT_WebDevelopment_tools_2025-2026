# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, select
from typing import List, Optional
import models
import connection
from models import (
    Warrior, WarriorDefault, Profession, WarriorProfessions,
    WarriorWithSkills, WarriorFull,
    Skill, SkillWarriorLink, RaceType
)
from connection import get_session

# Создаем экземпляр приложения FastAPI
app = FastAPI()

# Событие запуска приложения


@app.on_event("startup")
def on_startup():
    connection.init_db()

# Здесь могут быть определены эндпоинты (API-маршруты)
# Эндпоинты для воинов


@app.post("/warrior")
def warriors_create(warrior: WarriorDefault, session: Session = Depends(get_session)):
    """Создание нового воина."""
    new_warrior = Warrior.model_validate(warrior)
    session.add(new_warrior)
    session.commit()
    session.refresh(new_warrior)
    return {"status": 200, "data": new_warrior}


@app.get("/warriors_list")
def warriors_list(session: Session = Depends(get_session)) -> List[Warrior]:
    """Получение списка всех воинов."""
    return session.exec(select(Warrior)).all()


@app.get("/warrior/{warrior_id}", response_model=WarriorFull)
def warriors_get_full(warrior_id: int, session: Session = Depends(get_session)):
    """
    Получение воина по ID с вложенными профессией И умениями.
    Использует модель WarriorFull.
    """
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warrior with id {warrior_id} not found"
        )
    return warrior


@app.get("/warrior/{warrior_id}/with_profession", response_model=WarriorProfessions)
def warriors_get_with_profession(warrior_id: int, session: Session = Depends(get_session)):
    """
    Получение воина по ID только с профессией (без умений).
    Использует модель WarriorProfessions.
    """
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warrior with id {warrior_id} not found"
        )
    return warrior


@app.get("/warrior/{warrior_id}/with_skills", response_model=WarriorWithSkills)
def warriors_get_with_skills(warrior_id: int, session: Session = Depends(get_session)):
    """
    Получение воина по ID только с умениями (без профессии).
    Использует модель WarriorWithSkills.
    """
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warrior with id {warrior_id} not found"
        )
    return warrior


@app.patch("/warrior/{warrior_id}")  # Исправлен URL (добавлен слеш)
def warrior_update(warrior_id: int, warrior_data: WarriorDefault, session: Session = Depends(get_session)):
    """Частичное обновление данных воина."""
    db_warrior = session.get(Warrior, warrior_id)
    if not db_warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")

    # Проверяем, существует ли новая профессия
    if warrior_data.profession_id:
        profession = session.get(Profession, warrior_data.profession_id)
        if not profession:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profession with id {warrior_data.profession_id} not found"
            )

    update_data = warrior_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_warrior, key, value)

    session.add(db_warrior)
    session.commit()
    session.refresh(db_warrior)
    return db_warrior


@app.delete("/warrior/{warrior_id}")  # Исправлен URL (добавлен слеш)
def warrior_delete(warrior_id: int, session: Session = Depends(get_session)):
    """Удаление воина."""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    session.delete(warrior)
    session.commit()
    return {"ok": True}

# --- Эндпоинты для профессий ---


@app.get("/professions_list")
def professions_list(session: Session = Depends(get_session)) -> List[Profession]:
    """Получение списка всех профессий."""
    return session.exec(select(Profession)).all()


@app.get("/profession/{profession_id}")
def profession_get(profession_id: int, session: Session = Depends(get_session)):
    """Получение профессии по ID."""
    profession = session.get(Profession, profession_id)
    if not profession:
        raise HTTPException(status_code=404, detail="Profession not found")
    return profession


@app.post("/profession", status_code=status.HTTP_201_CREATED)
def profession_create(
    prof: models.Profession,  # Используем полную модель
    session: Session = Depends(get_session)
):
    """
    Создание новой профессии.
    
    Проверяет, не существует ли уже профессия с таким названием.
    """
    # Проверяем, есть ли уже такая профессия
    existing = session.exec(
        select(Profession).where(Profession.title == prof.title)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profession with title '{prof.title}' already exists"
        )

    session.add(prof)
    session.commit()
    session.refresh(prof)
    return {"status": 201, "data": prof}


@app.delete("/profession/{profession_id}")
def profession_delete(profession_id: int, session: Session = Depends(get_session)):
    """Удаление профессии."""
    profession = session.get(Profession, profession_id)
    if not profession:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profession with id {profession_id} not found"
        )

    # Проверяем, есть ли воины с этой профессией
    warriors_with_profession = session.exec(
        select(Warrior).where(Warrior.profession_id == profession_id)
    ).all()

    if warriors_with_profession:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete profession: {len(warriors_with_profession)} warriors have this profession"
        )

    session.delete(profession)
    session.commit()
    return {"ok": True, "message": f"Profession {profession_id} deleted"}


@app.get("/skills_list")
def skills_list(session: Session = Depends(get_session)) -> List[Skill]:
    """Получение списка всех умений."""
    return session.exec(select(Skill)).all()


@app.get("/skill/{skill_id}")
def skill_get(skill_id: int, session: Session = Depends(get_session)):
    """Получение умения по ID."""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )
    return skill


@app.post("/skill", status_code=status.HTTP_201_CREATED)
def skill_create(skill: Skill, session: Session = Depends(get_session)):
    """Создание нового умения."""
    # Проверяем, есть ли уже такое умение
    existing = session.exec(
        select(Skill).where(Skill.name == skill.name)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill with name '{skill.name}' already exists"
        )

    session.add(skill)
    session.commit()
    session.refresh(skill)
    return {"status": 201, "data": skill}


@app.delete("/skill/{skill_id}")
def skill_delete(skill_id: int, session: Session = Depends(get_session)):
    """Удаление умения."""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )

    # Проверяем, есть ли воины с этим умением
    warriors_with_skill = session.exec(
        select(Warrior).where(Warrior.id.in_(
            select(SkillWarriorLink.warrior_id).where(
                SkillWarriorLink.skill_id == skill_id)
        ))
    ).all()

    if warriors_with_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete skill: {len(warriors_with_skill)} warriors have this skill"
        )

    session.delete(skill)
    session.commit()
    return {"ok": True, "message": f"Skill {skill_id} deleted"}


@app.post("/warrior/{warrior_id}/skill/{skill_id}")
def add_skill_to_warrior(
    warrior_id: int,
    skill_id: int,
    session: Session = Depends(get_session)
):
    """
    Добавление умения воину через ассоциативную таблицу.
    
    Это создает запись в SkillWarriorLink, связывающую воина и умение.
    """
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warrior with id {warrior_id} not found"
        )

    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )

    # Проверяем, есть ли уже такое умение у воина
    if skill in warrior.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Warrior already has skill '{skill.name}'"
        )

    # Добавляем умение воину (автоматически создается запись в SkillWarriorLink)
    warrior.skills.append(skill)
    session.add(warrior)
    session.commit()
    session.refresh(warrior)

    return {
        "status": 200,
        "message": f"Skill '{skill.name}' added to warrior '{warrior.name}'",
        "warrior": warrior,
        "skill": skill
    }


@app.delete("/warrior/{warrior_id}/skill/{skill_id}")
def remove_skill_from_warrior(
    warrior_id: int,
    skill_id: int,
    session: Session = Depends(get_session)
):
    """
    Удаление умения у воина.
    
    Удаляет запись из ассоциативной таблицы SkillWarriorLink.
    """
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warrior with id {warrior_id} not found"
        )

    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )

    if skill not in warrior.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Warrior does not have skill '{skill.name}'"
        )

    # Удаляем умение у воина (автоматически удаляется запись из SkillWarriorLink)
    warrior.skills.remove(skill)
    session.add(warrior)
    session.commit()
    session.refresh(warrior)

    return {
        "status": 200,
        "message": f"Skill '{skill.name}' removed from warrior '{warrior.name}'",
        "warrior": warrior
    }


@app.get("/warrior/{warrior_id}/skills")
def get_warrior_skills(
    warrior_id: int,
    session: Session = Depends(get_session)
) -> List[Skill]:
    """
    Получение всех умений конкретного воина.
    
    Это демонстрирует работу с ассоциативной сущностью.
    """
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warrior with id {warrior_id} not found"
        )
    return warrior.skills


'''
temp_bd = [
    {
        "id": 1,
        "race": "director",
        "name": "Мартынов Дмитрий",
        "level": 12,
        "profession": {
            "id": 1,
            "title": "Влиятельный человек",
            "description": "Эксперт по всем вопросам"
        },
        "skills":
        [{
            "id": 1,
            "name": "Купле-продажа компрессоров",
            "description": ""

        },
            {
            "id": 2,
            "name": "Оценка имущества",
            "description": ""

        }]
    },
    {
        "id": 2,
        "race": "worker",
        "name": "Андрей Косякин",
        "level": 12,
        "profession": {
            "id": 1,
            "title": "Дельфист-гребец",
            "description": "Уважаемый сотрудник"
        },
        "skills": []
    },
]


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/warriors_list")
def warriors_list() -> List[Warrior]:
    return temp_bd


@app.get("/warrior/{warrior_id}")
def warriors_get(warrior_id: int) -> List[Warrior]:
    return [warrior for warrior in temp_bd if warrior.get("id") == warrior_id]


@app.post("/warrior")
def warriors_create(warrior: Warrior) -> ResponseWarrior:
    warrior_to_append = warrior.model_dump()
    temp_bd.append(warrior_to_append)
    return {"status": 200, "data": warrior}


@app.delete("/warrior/delete{warrior_id}")
def warrior_delete(warrior_id: int):
    for i, warrior in enumerate(temp_bd):
        if warrior.get("id") == warrior_id:
            temp_bd.pop(i)
            break
    return {"status": 201, "message": "deleted"}


@app.put("/warrior{warrior_id}")
def warrior_update(warrior_id: int, warrior: Warrior) -> List[Warrior]:
    for war in temp_bd:
        if war.get("id") == warrior_id:
            warrior_to_append = warrior.model_dump()
            temp_bd.remove(war)
            temp_bd.append(warrior_to_append)
    return temp_bd
'''
