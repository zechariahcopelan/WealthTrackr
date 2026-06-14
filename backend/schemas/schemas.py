from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ---------- Income Schemas ----------
class IncomeCreate(BaseModel):
    """Schema for creating a new income record."""
    source: str
    amount: float
    date_received: Optional[datetime] = None


class Income(BaseModel):
    """Schema for returning income data."""
    id: int
    source: str
    amount: float
    date_received: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncomeBatchCreate(BaseModel):
    """Schema for batch-creating multiple incomes."""
    incomes: List[IncomeCreate]


# ---------- Expense Schemas ----------
class ExpenseCreate(BaseModel):
    """Schema for creating an expense."""
    name: str
    description: Optional[str] = None
    amount: float
    date: datetime
    category_id: int
    is_recurring: Optional[bool] = False
    frequency: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class Expense(BaseModel):
    """Schema for returning expense data."""
    id: int
    name: str
    description: Optional[str] = None
    amount: float
    date: datetime
    category_id: int
    is_recurring: Optional[bool] = False
    frequency: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Token Schemas ----------
class Token(BaseModel):
    """Access token returned after login or refresh."""
    access_token: str
    token_type: str


class TokenWithRefresh(Token):
    """Access + refresh token combo for login response."""
    refresh_token: str


class TokenData(BaseModel):
    """Payload extracted from JWT."""
    username: Optional[str] = None
    exp: Optional[int] = None  # Useful for future token expiration handling


# ---------- User Schemas ----------
class UserBase(BaseModel):
    """Shared properties for user."""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Used when creating a new user."""
    password: str


class User(UserBase):
    """Returned user schema."""
    id: int

    class Config:
        from_attributes = True


# ---------- User Login Schema ----------
class UserLogin(BaseModel):
    """Login payload for users."""
    username: str
    password: str


# ---------- Category Schemas ----------
class CategoryBase(BaseModel):
    """Shared properties for categories."""
    name: str


class CategoryCreate(CategoryBase):
    """Used to create a new category."""
    pass


class Category(CategoryBase):
    """Returned category schema."""
    id: int

    class Config:
        from_attributes = True




