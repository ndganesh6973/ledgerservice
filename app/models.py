from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from .database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)
    currency = Column(String(3), nullable=False)

    __table_args__ = (
        CheckConstraint('balance >= 0', name='check_minimum_balance'),
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(String, nullable=False)
    idempotency_key = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('account_id', 'idempotency_key', name='uix_account_idempotency'),
    )