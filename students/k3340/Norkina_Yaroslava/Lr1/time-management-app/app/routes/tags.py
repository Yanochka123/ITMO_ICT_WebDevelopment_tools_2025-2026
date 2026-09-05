# app/routes/tags.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud, models
from app.database import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/", response_model=List[schemas.TagResponse])
def get_tags(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_tags(db, user_id=current_user.id)

@router.post("/", response_model=schemas.TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_tag(db, tag, user_id=current_user.id)

@router.patch("/{tag_id}", response_model=schemas.TagResponse)
def update_tag(
    tag_id: int,
    tag_update: schemas.TagUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_tag = crud.update_tag(db, tag_id, tag_update)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db_tag

@router.delete("/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_tag = crud.delete_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted successfully"}