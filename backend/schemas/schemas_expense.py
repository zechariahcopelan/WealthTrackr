from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date

class ExpenseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    amount: float
    is_recurring: bool = False
    frequency: Optional[Literal["weekly", "monthly", "annually", "one_time"]] = "one_time"
    payment_method: Optional[str] = None
    date: date
    notes: Optional[str] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    class Config:
        from_attributes = True


class ExpenseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    amount: float
    is_recurring: bool
    frequency: Optional[str] = None
    payment_method: Optional[str] = None
    date: date
    notes: Optional[str] = None
    user_id: int

    class Config:
        from_attributes = True
        use_enum_values = True


class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    amount: Optional[float] = None
    is_recurring: Optional[bool] = None
    frequency: Optional[Literal["weekly", "monthly", "annually", "one_time"]] = None
    payment_method: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2) if v is not None else v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v is not None else v

    class Config:
        from_attributes = True



