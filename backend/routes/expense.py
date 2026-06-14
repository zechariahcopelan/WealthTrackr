# backend/routes/expense.py

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session # SQLAlchemy’s DB session type for queries.
from typing import List #Type hint for returning lists of responses.
import logging


#ExpenseCreate: Pydantic model that defines what a user must provide to create an expense.
#ExpenseResponse: Schema used to shape the output sent back to the client.
from backend.schemas.schemas_expense import ExpenseCreate, ExpenseResponse
from backend.models.models_user import User
from backend.database import get_db
from backend.auth import get_current_user #Auth dependency to extract the user from the access token.
from backend.crud_expense import create_expense, get_expenses

#Tagged "Expenses" for Swagger UI.
router = APIRouter(prefix="/expenses", tags=["Expenses"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=ExpenseResponse)
#creates a new expense for the currently authenticated user.
def create_expense_entry(
    expense_data: ExpenseCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    #Passes the sanitized input to your CRUD logic (create_expense).
    return create_expense(db, expense_data=expense_data, user_id=current_user.id)

@router.get("/", response_model=List[ExpenseResponse])
#Returns a list of expenses for the authenticated user.
def get_user_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return get_expenses(db, user_id=current_user.id, skip=skip, limit=limit)
