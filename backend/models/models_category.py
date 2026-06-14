# backend/models/models_category.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "wealthtrackr"}  # Added schema specification

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # Added index=True for consistency and performance
    # Foreign Key to link this category to a specific user
    user_id = Column(Integer, ForeignKey("wealthtrackr.users.id"), nullable=False)  # Fixed: Added schema to foreign key

    # Defines the many-to-one relationship with the User model
    # 'user' is the attribute on the Category object that will hold the User object
    # 'back_populates="categories"' links this back to the 'categories' relationship defined in the User model
    user = relationship("User", back_populates="categories")

    # Existing relationship to Expense model
    expenses = relationship("Expense", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', user_id={self.user_id})>"
