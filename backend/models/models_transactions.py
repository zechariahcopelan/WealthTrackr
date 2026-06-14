from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from backend.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # "income" or "expense"
    description = Column(String)
    date = Column(DateTime, nullable=False)
