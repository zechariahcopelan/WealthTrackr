# backend/routes/income.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.schemas.schemas_income import IncomeCreate, IncomeResponse
from backend.models.models_user import User
from backend.database import get_db
from backend.auth import get_current_user
from backend.crud_income import create_income, get_incomes

router = APIRouter(prefix="/incomes", tags=["Incomes"])

@router.post("/", response_model=IncomeResponse)
def create_income_entry(
    income: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return create_income(db, income, user_id=current_user.id)

@router.get("/", response_model=List[IncomeResponse])
def get_income_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return get_incomes(db, user_id=current_user.id)
