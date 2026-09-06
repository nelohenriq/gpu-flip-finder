from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean
from sqlalchemy.sql import func
from src.db.session import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    condition = Column(String, nullable=True)
    location = Column(String, nullable=True)
    seller = Column(String, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    raw = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())


class Comp(Base):
    __tablename__ = "comps"

    id = Column(String, primary_key=True)
    model = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    source = Column(String, nullable=True)
    url = Column(Text, nullable=True)
    captured_at = Column(DateTime, server_default=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    listing_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    model = Column(String, nullable=True)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=True)
    fees = Column(Float, default=0.0)
    shipping = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    status = Column(String, nullable=False, default="listed")
    notes = Column(Text, nullable=True)
    bought_at = Column(DateTime, server_default=func.now())
    sold_at = Column(DateTime, nullable=True)
