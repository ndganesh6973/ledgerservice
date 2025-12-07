
from sqlalchemy import select, func
from . import models

async def create_account(db, currency):
    acc = models.Account(currency=currency.upper())
    db.add(acc)
    await db.flush()
    return acc

async def get_account(db, id):
    return await db.get(models.Account, id)

async def get_balance(db, id):
    q = select(func.sum(models.LedgerEntry.amount)).where(models.LedgerEntry.account_id == id)
    res = await db.execute(q)
    return res.scalar() or 0
