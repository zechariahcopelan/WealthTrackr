# /home/kenneth-copeland/Documents/WealthTrackr/backend/models/__init__.py

# Import Base from the database module (it's not in the models folder)
from ..database import Base

# Import individual models from their respective files within the same 'models' package
from .models_user import User
from .models_income import Income
from .models_expense import Expense
from .models_category import Category # Assuming you have a models_category.py file
