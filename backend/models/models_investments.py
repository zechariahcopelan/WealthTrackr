from sqlalchemy import Column, Integer, String, Float, Date, Enum
from backend.database import Base
import enum

class AssetTypeEnum(str, enum.Enum):
    stock = "stock"
    crypto = "crypto"
    real_estate = "real_estate"
    other = "other"

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    asset_name = Column(String, nullable=False)
    asset_type = Column(Enum(AssetTypeEnum), nullable=False)
    quantity = Column(Float, nullable=True)
    amount_invested = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=True)
    purchase_date = Column(Date, nullable=True)
    current_price = Column(Float, nullable=True)
    total_invested = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)
    brokerage = Column(String, nullable=True)
    notes = Column(String, nullable=True)
