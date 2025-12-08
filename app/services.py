from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from . import models

def execute_transfer(db: Session, from_account_id: int, to_account_id: int, amount: Decimal, idempotency_key: str):
    # 1. Idempotency Check
    existing_tx = db.query(models.Transaction).filter(
        models.Transaction.idempotency_key == idempotency_key
    ).first()
    
    if existing_tx:
        return {"status": "SKIPPED", "message": "Transaction already processed"}

    # 2. Lock Accounts (Sort IDs to prevent Deadlocks)
    first_id, second_id = sorted([from_account_id, to_account_id])
    
    a1 = db.query(models.Account).with_for_update().filter(models.Account.id == first_id).first()
    a2 = db.query(models.Account).with_for_update().filter(models.Account.id == second_id).first()

    sender = a1 if a1.id == from_account_id else a2
    receiver = a2 if a2.id == to_account_id else a1

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="One or both accounts not found")

    # 3. Check Balance
    if sender.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # 4. Execute Transfer
    sender.balance -= amount
    receiver.balance += amount

    # Force DB to track updates
    db.add(sender)
    db.add(receiver)

    # 5. Audit Trail (Double Entry)
    debit = models.Transaction(
        account_id=sender.id, amount=-amount, transaction_type="TRANSFER_OUT", idempotency_key=f"{idempotency_key}_db"
    )
    credit = models.Transaction(
        account_id=receiver.id, amount=amount, transaction_type="TRANSFER_IN", idempotency_key=f"{idempotency_key}_cr"
    )
    main_record = models.Transaction(
        account_id=sender.id, amount=0, transaction_type="TRANSFER_LOG", idempotency_key=idempotency_key
    )

    db.add(debit)
    db.add(credit)
    db.add(main_record)
    
    db.commit()
    db.refresh(sender)
    
    return {"status": "success", "sender_new_balance": sender.balance}