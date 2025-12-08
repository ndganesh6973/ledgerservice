from pydantic import BaseModel, validator
from typing import Optional
from decimal import Decimal
from datetime import datetime

# --- INPUTS ---

class AccountBase(BaseModel):
    owner: str
    currency: str

class AccountCreate(AccountBase):
    @validator('currency')
    def validate_currency(cls, v):
        if v not in ['USD', 'INR']:
            raise ValueError('Currency must be USD or INR')
        return v

class TransactionCreate(BaseModel):
    account_id: int
    amount: Decimal
    # Removed 'type' because main.py sets it automatically (DEPOSIT/WITHDRAWAL)
    idempotency_key: str

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal
    idempotency_key: str

# --- OUTPUTS ---

class AccountResponse(AccountBase):
    id: int
    balance: Decimal
    
    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    account_id: int
    amount: Decimal
    transaction_type: str
    idempotency_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True