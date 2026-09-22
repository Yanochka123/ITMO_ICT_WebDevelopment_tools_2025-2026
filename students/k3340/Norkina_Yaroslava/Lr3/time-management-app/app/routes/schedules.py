# app/routes/schedules.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app import schemas, crud, models
from app.database import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.get("/", response_model=List[schemas.DailyScheduleResponse])
def get_schedules(
    date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_daily_schedules(db, user_id=current_user.id, date=date)

@router.post("/", response_model=schemas.DailyScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    schedule: schemas.DailyScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_daily_schedule(db, schedule, user_id=current_user.id)

@router.patch("/{schedule_id}", response_model=schemas.DailyScheduleResponse)
def update_schedule(
    schedule_id: int,
    schedule_update: schemas.DailyScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_schedule = crud.update_daily_schedule(db, schedule_id, schedule_update)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_schedule = crud.delete_daily_schedule(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted successfully"}