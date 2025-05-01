from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app import schemas
from app.models import User, Account, Payment

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",
    crypt__disabled=True
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(User).filter(User.email == email)
    )
    return result.scalars().first()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_users_with_accounts(
        db: AsyncSession, skip: int = 0, limit: int = 100
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.accounts))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def crud_create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_admin=user.is_admin
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def crud_update_user(db: AsyncSession, user_id: int,
                           user: schemas.UserUpdate):
    db_user = await get_user(db, user_id)
    if user.email:
        db_user.email = user.email
    if user.full_name:
        db_user.full_name = user.full_name
    if user.password:
        db_user.hashed_password = get_password_hash(user.password)

    await db.commit()
    await db.refresh(db_user)
    return db_user


async def crud_delete_user(db: AsyncSession, user_id: int):
    db_user = await get_user(db, user_id)
    await db.delete(db_user)
    await db.commit()
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# Account operations
async def get_account(db: AsyncSession, account_id: int):
    result = await db.execute(
        select(Account).filter(Account.id == account_id)
    )
    return result.scalars().first()


async def get_user_accounts(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Account).filter(Account.user_id == user_id)
    )
    return result.scalars().all()


async def create_account(db: AsyncSession, account_id: int, user_id: int,
                         balance: float = 0.0):
    db_account = Account(id=account_id, user_id=user_id,
                         balance=balance)
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account


async def update_account_balance(db: AsyncSession, account_id: int,
                                 amount: float):
    db_account = await get_account(db, account_id)
    db_account.balance += amount
    await db.commit()
    await db.refresh(db_account)
    return db_account


# Payment operations
async def get_payment(db: AsyncSession, payment_id: int):
    result = await db.execute(
        select(Payment).filter(Payment.id == payment_id)
    )
    return result.scalars().first()


async def get_payment_by_transaction_id(db: AsyncSession, transaction_id: str):
    result = await db.execute(
        select(Payment)
        .filter(Payment.transaction_id == transaction_id)
    )
    return result.scalars().first()


async def get_user_payments(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Payment)
        .filter(Payment.user_id == user_id)
    )
    return result.scalars().all()


async def create_payment(db: AsyncSession, transaction_id: str,
                         account_id: int, user_id: int, amount: float):
    db_payment = Payment(
        transaction_id=transaction_id,
        account_id=account_id,
        user_id=user_id,
        amount=amount
    )
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment
