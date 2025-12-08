from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database, services
from scalar_fastapi import get_scalar_api_reference

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Ledger Service API",
    description="""
    A high-integrity double-entry bookkeeping system.
    
    ## Features
    * **Accounts**: Create and manage USD/INR accounts.
    * **Deposit/Withdraw**: Add or remove funds securely.
    * **Transfers**: Atomic money movement between users.
    * **History**: Full audit trail of transactions.
    """,
    version="1.0.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"}
)

@app.get("/")
def read_root():
    return {"message": "System is Online"}

@app.post("/accounts/", response_model=schemas.AccountResponse)
def create_account(account: schemas.AccountCreate, db: Session = Depends(database.get_db)):
    db_account = models.Account(owner=account.owner, currency=account.currency, balance=0.00)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@app.get("/accounts/{account_id}", response_model=schemas.AccountResponse)
def get_balance(account_id: int, db: Session = Depends(database.get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.post("/deposit/")
def deposit_funds(transaction: schemas.TransactionCreate, db: Session = Depends(database.get_db)):
    account = db.query(models.Account).with_for_update().filter(models.Account.id == transaction.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    account.balance += transaction.amount
    
    entry = models.Transaction(
        account_id=account.id, 
        amount=transaction.amount, 
        transaction_type="DEPOSIT", 
        idempotency_key=transaction.idempotency_key
    )
    
    db.add(entry)
    db.add(account) 
    db.commit()
    db.refresh(account) 
    return {"status": "success", "new_balance": account.balance}

@app.post("/withdraw/")
def withdraw_funds(transaction: schemas.TransactionCreate, db: Session = Depends(database.get_db)):
    account = db.query(models.Account).with_for_update().filter(models.Account.id == transaction.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
        
    account.balance -= transaction.amount
    
    entry = models.Transaction(
        account_id=account.id, 
        amount=-transaction.amount,
        transaction_type="WITHDRAWAL", 
        idempotency_key=transaction.idempotency_key
    )
    
    db.add(entry)
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"status": "success", "new_balance": account.balance}

@app.post("/transfer/")
def transfer_funds(transfer: schemas.TransferCreate, db: Session = Depends(database.get_db)):
    return services.execute_transfer(
        db, transfer.from_account_id, transfer.to_account_id, transfer.amount, transfer.idempotency_key
    )

@app.get("/accounts/{account_id}/history", response_model=List[schemas.TransactionResponse])
def get_history(account_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    return db.query(models.Transaction)\
        .filter(models.Transaction.account_id == account_id)\
        .order_by(models.Transaction.created_at.desc())\
        .offset(skip).limit(limit).all()

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )