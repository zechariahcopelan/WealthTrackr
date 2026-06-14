# backend/models/models_expense.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = {"schema": "wealthtrackr"}  # Added schema specification

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("wealthtrackr.users.id"), nullable=False)  # Fixed: Added schema to foreign key
    category_id = Column(Integer, ForeignKey("wealthtrackr.categories.id"))  # Fixed: Added schema to foreign key
    amount = Column(Float, nullable=False)
    description = Column(String)
    date_spent = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")

    def __repr__(self):
        return f"<Expense(id={self.id}, description='{self.description}', amount={self.amount}, user_id={self.user_id})>"
