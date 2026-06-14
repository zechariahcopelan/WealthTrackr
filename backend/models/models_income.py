# backend/models/models_income.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Income(Base):
    __tablename__ = "incomes"
    __table_args__ = {"schema": "wealthtrackr"}  # Added schema specification

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("wealthtrackr.users.id"), nullable=False)  # Fixed: Added schema to foreign key
    source = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date_received = Column(DateTime, nullable=False)

    # Defines the many-to-one relationship with the User model
    # 'user' is the attribute on the Income object that will hold the User object
    # 'back_populates="incomes"' links this back to the 'incomes' relationship defined in the User model
    user = relationship("User", back_populates="incomes")

    def __repr__(self):
        return f"<Income(id={self.id}, source='{self.source}', amount={self.amount}, user_id={self.user_id})>"
