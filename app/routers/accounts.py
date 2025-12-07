from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import AsyncSessionLocal
from .. import crud, schemas

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/", response_model=schemas.AccountOut)
async def create_account(payload: schemas.AccountCreate, db: AsyncSession = Depends(get_db)):
    acc = await crud.create_account(db, payload.currency)
    await db.commit()
    return acc

@router.get("/{id}/balance")
async def balance(id: int, db: AsyncSession = Depends(get_db)):
    bal = await crud.get_balance(db, id)
    return {"balance": float(bal)}