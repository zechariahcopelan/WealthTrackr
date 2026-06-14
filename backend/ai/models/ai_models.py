# backend/ai/models/ai_models.py

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class AIInsight(Base):
    """Store AI-generated insights for users"""
    __tablename__ = "ai_insights"
    __table_args__ = {"schema": "wealthtrackr"}
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("wealthtrackr.users.id"), nullable=False)
    insight_type = Column(String(50), nullable=False)  # 'spending', 'budget', 'investment', 'subscription'
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")  # 'low', 'medium', 'high', 'urgent'
    potential_savings = Column(Float, nullable=True)  # Estimated savings amount
    confidence_score = Column(Float, default=0.8)  # AI confidence 0-1
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    insight_metadata = Column(JSON, nullable=True)  # Additional data for the insight
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationship with cascade delete
    user = relationship("User", back_populates="ai_insights")
    
    def __repr__(self):
        return f"<AIInsight(id={self.id}, type='{self.insight_type}', user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if insight has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def age_days(self) -> int:
        """Get age of insight in days"""
        return (datetime.utcnow() - self.created_at).days

class UserFinancialProfile(Base):
    """Store user's financial profile for AI analysis"""
    __tablename__ = "user_financial_profiles"
    __table_args__ = {"schema": "wealthtrackr"}
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("wealthtrackr.users.id"), nullable=False, unique=True)
    
    # Risk Assessment
    risk_tolerance = Column(String(20), default="moderate")  # 'conservative', 'moderate', 'aggressive'
    investment_experience = Column(String(20), default="beginner")  # 'beginner', 'intermediate', 'advanced'
    investment_goals = Column(JSON, nullable=True)  # ['retirement', 'house', 'emergency_fund', etc.]
    
    # Financial Metrics (calculated by AI)
    monthly_income_avg = Column(Float, default=0.0)
    monthly_expenses_avg = Column(Float, default=0.0)
    savings_rate = Column(Float, default=0.0)  # Percentage
    debt_to_income_ratio = Column(Float, default=0.0)
    
    # Spending Patterns
    top_expense_categories = Column(JSON, nullable=True)  # [{'category': 'food', 'percentage': 30}, ...]
    spending_volatility = Column(Float, default=0.0)  # Standard deviation of monthly spending
    
    # Investment Preferences
    preferred_sectors = Column(JSON, nullable=True)  # ['technology', 'healthcare', etc.]
    max_single_investment_amount = Column(Float, default=1000.0)
    emergency_fund_target = Column(Float, default=5000.0)
    
    # AI Insights
    financial_health_score = Column(Float, default=50.0)  # 0-100 score
    last_analysis_date = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="financial_profile")
    
    def __repr__(self):
        return f"<UserFinancialProfile(user_id={self.user_id}, health_score={self.financial_health_score})>"
    
    @property
    def monthly_surplus(self) -> float:
        """Calculate monthly financial surplus"""
        return max(0, self.monthly_income_avg - self.monthly_expenses_avg)
    
    @property
    def financial_health_grade(self) -> str:
        """Get letter grade for financial health"""
        if self.financial_health_score >= 90:
            return "A+"
        elif self.financial_health_score >= 80:
            return "A"
        elif self.financial_health_score >= 70:
            return "B"
        elif self.financial_health_score >= 60:
            return "C"
        elif self.financial_health_score >= 50:
            return "D"
        else:
            return "F"
    
    @property
    def needs_emergency_fund(self) -> bool:
        """Check if user needs to build emergency fund"""
        emergency_fund_needed = self.monthly_expenses_avg * 6
        return self.emergency_fund_target < emergency_fund_needed

class SubscriptionAlternative(Base):
    """Database of subscription services and their alternatives"""
    __tablename__ = "subscription_alternatives"
    __table_args__ = {"schema": "wealthtrackr"}
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # 'streaming', 'fitness', 'software', etc.
    price_monthly = Column(Float, nullable=False)
    features = Column(JSON, nullable=True)  # List of features
    
    # Alternative suggestions
    alternative_to = Column(String(100), nullable=True, index=True)  # What service this replaces
    savings_amount = Column(Float, nullable=True)  # Monthly savings compared to alternative_to
    pros = Column(JSON, nullable=True)  # List of advantages
    cons = Column(JSON, nullable=True)  # List of disadvantages
    
    # Service metadata
    website_url = Column(String(200), nullable=True)
    signup_bonus = Column(String(200), nullable=True)
    free_trial_days = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SubscriptionAlternative(service='{self.service_name}', price=${self.price_monthly})>"
    
    @property
    def annual_cost(self) -> float:
        """Calculate annual cost"""
        return self.price_monthly * 12
    
    @property
    def annual_savings(self) -> float:
        """Calculate annual savings compared to alternative"""
        if not self.savings_amount:
            return 0.0
        return self.savings_amount * 12

class InvestmentRecommendation(Base):
    """AI-generated investment recommendations for users"""
    __tablename__ = "investment_recommendations"
    __table_args__ = {"schema": "wealthtrackr"}
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("wealthtrackr.users.id"), nullable=False)
    
    # Investment Details
    symbol = Column(String(10), nullable=False)  # Stock/ETF symbol
    name = Column(String(200), nullable=False)
    investment_type = Column(String(30), nullable=False)  # 'stock', 'etf', 'mutual_fund', 'bond'
    sector = Column(String(50), nullable=True)
    
    # AI Analysis
    recommendation_type = Column(String(20), nullable=False)  # 'buy', 'hold', 'avoid'
    confidence_score = Column(Float, nullable=False)  # 0-1
    risk_level = Column(String(20), nullable=False)  # 'low', 'medium', 'high'
    
    # Financial Metrics
    current_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=True)
    expected_return_1y = Column(Float, nullable=True)  # Percentage
    dividend_yield = Column(Float, nullable=True)
    
    # Reasoning
    reason_summary = Column(Text, nullable=False)
    key_factors = Column(JSON, nullable=True)  # List of factors supporting the recommendation
    risks = Column(JSON, nullable=True)  # List of potential risks
    
    # Recommendation Details
    suggested_allocation = Column(Float, nullable=True)  # Percentage of portfolio
    min_investment_amount = Column(Float, default=100.0)
    time_horizon = Column(String(20), default="long_term")  # 'short_term', 'medium_term', 'long_term'
    
    # Status
    is_active = Column(Boolean, default=True)
    is_user_interested = Column(Boolean, nullable=True)  # User feedback
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="investment_recommendations")
    
    def __repr__(self):
        return f"<InvestmentRecommendation(symbol='{self.symbol}', type='{self.recommendation_type}', user_id={self.user_id})>"
    
    @property
    def potential_return_amount(self) -> float:
        """Calculate potential return amount for 1 year"""
        if not self.expected_return_1y or not self.min_investment_amount:
            return 0.0
        return self.min_investment_amount * (self.expected_return_1y / 100)
    
    @property
    def is_expired(self) -> bool:
        """Check if recommendation has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def confidence_level(self) -> str:
        """Get confidence level as string"""
        if self.confidence_score >= 0.9:
            return "Very High"
        elif self.confidence_score >= 0.8:
            return "High"
        elif self.confidence_score >= 0.7:
            return "Medium"
        elif self.confidence_score >= 0.6:
            return "Low"
        else:
            return "Very Low"
