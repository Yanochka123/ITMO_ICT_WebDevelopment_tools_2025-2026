# app/routes/analytics.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app import schemas, crud, models
from app.database import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/weekly-summary", response_model=schemas.WeeklySummaryResponse)
def get_weekly_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_weekly_summary(db, user_id=current_user.id)

@router.get("/productivity-trend")
def get_productivity_trend(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_productivity_trend(db, user_id=current_user.id, days=days)

@router.get("/category-breakdown", response_model=schemas.CategoryBreakdownResponse)
def get_category_breakdown(
    start_date: datetime = Query(default_factory=lambda: datetime.utcnow() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=datetime.utcnow),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_category_breakdown(db, user_id=current_user.id, start_date=start_date, end_date=end_date)