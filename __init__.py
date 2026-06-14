# /home/kenneth-copeland/Documents/WealthTrackr/WealthTrackr/__init__.py
from .backend.main import app  # Expose the FastAPI app if needed
from .models import User, Income, Expense, Category  # Expose models
from .schemas.schemas_income import IncomeInput, IncomeCreate, IncomeResponse
from .schemas.schemas_expense import ExpenseCreate, ExpenseResponse
