from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import database, models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.AccountResponse)
def create_account(account: schemas.AccountCreate, db: Session = Depends(database.get_db)):
   
    db_account = models.Account(owner=account.owner, currency=account.currency, balance=0.00)
    

    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    return db_account

@router.get("/{account_id}/balance")
def get_balance(account_id: int, db: Session = Depends(database.get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"balance": account.balance}