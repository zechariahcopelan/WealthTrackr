from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
from typing import TYPE_CHECKING

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from backend.ai.models.ai_models import AIInsight, UserFinancialProfile, InvestmentRecommendation

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "wealthtrackr"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Email verification fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)
    verification_sent_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Core Financial Relationships
    incomes = relationship("Income", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
    categories = relationship("Category", back_populates="user")
    
    # AI Relationships - NEW: AI-powered financial features
    ai_insights = relationship("AIInsight", back_populates="user", cascade="all, delete-orphan")
    financial_profile = relationship("UserFinancialProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    investment_recommendations = relationship("InvestmentRecommendation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', verified={self.is_verified})>"
    
    @property
    def has_ai_profile(self) -> bool:
        """Check if user has an AI financial profile"""
        return self.financial_profile is not None
    
    @property
    def unread_insights_count(self) -> int:
        """Get count of unread AI insights"""
        if not self.ai_insights:
            return 0
        return sum(1 for insight in self.ai_insights if not insight.is_read and not insight.is_dismissed)
    
    @property
    def total_potential_savings(self) -> float:
        """Calculate total potential savings from all active insights"""
        if not self.ai_insights:
            return 0.0
        return sum(
            insight.potential_savings or 0.0 
            for insight in self.ai_insights 
            if not insight.is_dismissed and insight.potential_savings
        )
