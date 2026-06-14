from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base
from backend.database import Base
import enum

class TipCategoryEnum(str, enum.Enum):
    spending_alert = "spending_alert"
    investment_opportunity = "investment_opportunity"
    budget_suggestion = "budget_suggestion"

class TipSeverityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class FinancialTip(Base):
    __tablename__ = "financial_tips"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    category = Column(Enum(TipCategoryEnum), nullable=True)
    severity = Column(Enum(TipSeverityEnum), nullable=True)
    related_income_id = Column(Integer, ForeignKey("incomes.id"), nullable=True)
    related_expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)
    related_investment_id = Column(Integer, ForeignKey("investments.id"), nullable=True)
    source = Column(String, nullable=True)
