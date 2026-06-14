from sqlalchemy.orm import Session
from typing import List
import datetime

from backend.models.models_income import Income
from backend.models.models_user import User

from backend.schemas.schemas import IncomeCreate
from backend.schemas.schemas import Income as IncomeResponseSchema
from backend.schemas.schemas import IncomeBatchCreate


def _map_income_create_to_model_dict(income_data: IncomeCreate) -> dict:
    income_dict = income_data.model_dump(exclude_unset=True)

    if 'description' in income_dict and 'source' not in income_dict:
        income_dict['source'] = income_dict.pop('description')
    
    if 'source' not in income_dict or not income_dict['source']:
        income_dict['source'] = 'Unknown Source'

    if 'date' in income_dict:
        if 'date_received' not in income_dict:
            income_dict['date_received'] = income_dict.pop('date')
        else:
            del income_dict['date']
    
    if 'date_received' in income_dict and isinstance(income_dict['date_received'], datetime.datetime):
        income_dict['date_received'] = income_dict['date_received'].date()

    fields_to_remove = ['description', 'date']
    for field in fields_to_remove:
        if field in income_dict:
            del income_dict[field]

    return income_dict

def create_income(db: Session, income_data: IncomeCreate, user_id: int):
    income_dict = _map_income_create_to_model_dict(income_data)
    db_income = Income(**income_dict, user_id=user_id)
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income

def create_income_entries(db: Session, income_list: List[IncomeCreate], user_id: int):
    created_incomes = []
    for income_data in income_list:
        income_dict = _map_income_create_to_model_dict(income_data)
        db_income = Income(**income_dict, user_id=user_id)
        db.add(db_income)
        created_incomes.append(db_income)
    
    db.commit()
    for income in created_incomes:
        db.refresh(income)
    return created_incomes

def get_incomes(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Income).filter(Income.user_id == user_id).offset(skip).limit(limit).all()

def get_income_by_id(db: Session, income_id: int, user_id: int):
    return db.query(Income).filter(Income.id == income_id, Income.user_id == user_id).first()

def update_income(db: Session, income_id: int, income_data: IncomeCreate, user_id: int):
    income = db.query(Income).filter(Income.id == income_id, Income.user_id == user_id).first()
    if income:
        update_dict = _map_income_create_to_model_dict(income_data)
        for field, value in update_dict.items():
            setattr(income, field, value)
        db.commit()
        db.refresh(income)
    return income

def delete_income(db: Session, income_id: int, user_id: int):
    income = db.query(Income).filter(Income.id == income_id, Income.user_id == user_id).first()
    if income:
        db.delete(income)
        db.commit()
        return True
    return False

