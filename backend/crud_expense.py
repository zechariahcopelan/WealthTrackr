# ~/Documents/WealthTrackr/backend/crud_expense.py

from sqlalchemy.orm import Session
from typing import List
from backend.models.models_expense import Expense
from backend.models.models_category import Category
from backend.models.models_user import User
from backend.schemas.schemas_expense import ExpenseCreate, ExpenseUpdate


def create_expense(db: Session, expense_data: ExpenseCreate, user_id: int):
    """Create a new expense entry for a user"""
    expense = Expense(
        name=expense_data.name,
        description=expense_data.description,  # New field
        amount=expense_data.amount,
        date=expense_data.date,
        category_id=expense_data.category_id,
        user_id=user_id,
        is_recurring=expense_data.is_recurring,
        frequency=expense_data.frequency,
        payment_method=expense_data.payment_method,
        notes=expense_data.notes
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expenses(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get expenses for a specific user with pagination"""
    try:
        return db.query(Expense).filter(Expense.user_id == user_id).offset(skip).limit(limit).all()
    except Exception as e:
        print(f"Error getting expenses: {e}")
        return []


def get_expense_by_id(db: Session, expense_id: int, user_id: int):
    """Get a specific expense entry by ID for a user"""
    return db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()


def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate, user_id: int):
    """Update an existing expense entry"""
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
    if expense:
        for field, value in expense_data.dict(exclude_unset=True).items():
            setattr(expense, field, value)
        db.commit()
        db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int, user_id: int):
    """Delete an expense entry"""
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
    if expense:
        db.delete(expense)
        db.commit()
        return True
    return False


def get_expenses_by_category(db: Session, user_id: int, category_name: str, skip: int = 0, limit: int = 100):
    """Get expenses for a user filtered by category name"""
    return db.query(Expense).join(Category).filter(
        Expense.user_id == user_id,
        Category.name == category_name
    ).offset(skip).limit(limit).all()


def get_expenses_by_date_range(db: Session, user_id: int, start_date, end_date, skip: int = 0, limit: int = 100):
    """Get expenses for a user within a date range"""
    return db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).offset(skip).limit(limit).all()


