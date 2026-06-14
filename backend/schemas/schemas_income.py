# /home/kenneth-copeland/Documents/WealthTrackr/schemas/schemas_income.py
from pydantic import BaseModel, validator
from typing import Optional, Literal, List
from datetime import date

# This is for creating a single income entry
class IncomeCreate(BaseModel):
    source: str  # Made required to enforce data entry
    amount: float
    date_received: date  # Renamed from 'date' to match model and API usage
    is_recurring: bool = False
    frequency: Optional[Literal["weekly", "monthly", "annually", "one_time"]] = "one_time"
    type: Optional[Literal["active", "passive"]] = "active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    last_received_date: Optional[date] = None
    notes: Optional[str] = None
    description: Optional[str] = None  # Kept for compatibility, but not used in model

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)

    @validator('source', always=True)
    def set_source(cls, v, values):
        # If source is not provided, raise an error instead of defaulting
        if not v and not values.get('description'):
            raise ValueError('source is required')
        return v or values.get('description', "Unknown Source")

    @validator('last_received_date', always=True)
    def set_last_received_date(cls, v, values):
        # Use date_received if last_received_date is not provided
        if not v and values.get('date_received'):
            return values['date_received']
        return v

    class Config:
        from_attributes = True

# This is what IncomeInput should look like for batch creation
class IncomeInput(BaseModel):
    incomes: List[IncomeCreate]

    class Config:
        from_attributes = True

# This is for returning income data
class IncomeResponse(BaseModel):
    id: int
    source: str
    amount: float
    is_recurring: bool
    frequency: Optional[str]  # Changed from Literal to str to handle Enums
    type: Optional[str]       # Changed from Literal to str to handle Enums
    start_date: Optional[date]
    end_date: Optional[date]
    last_received_date: Optional[date]
    notes: Optional[str]
    user_id: int

    class Config:
        from_attributes = True
        use_enum_values = True  # This converts Enums to their string values
