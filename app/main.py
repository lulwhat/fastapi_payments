from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import AsyncGenerator

from app import schemas
from app.crud import get_user_by_email, authenticate_user, get_user_accounts, \
    get_user_payments, get_users_with_accounts, get_user, \
    get_payment_by_transaction_id, get_account, create_account, \
    create_payment, update_account_balance, crud_create_user, \
    crud_update_user, crud_delete_user
from app.database import get_db
from app.logger import get_logger
from app.models import User
from app.security import security_schemes, get_current_user, \
    get_current_admin, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, \
    calculate_payment_signature


logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await logger.info("Starting application...")
    await logger.initialize()

    yield

    await logger.info("Shutting down application...")
    await logger.shutdown()

app = FastAPI(
    title="Payment System API",
    lifespan=lifespan,
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "clientId": "your-client-id",
        "appName": "Payment System API"
    },
    security_schemes=security_schemes,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "withCredentials": True
    }
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication endpoint
@app.post(
    "/token",
    response_model=schemas.Token,
    description="""## Authorize and set auth token:
    
        - username - email you registered with
        - password - password
    """
)
async def login_for_access_token(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(
        db,
        form_data.username,
        form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(data={"sub": user.email})

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=int(ACCESS_TOKEN_EXPIRE_MINUTES.total_seconds()),
        secure=True,
        samesite="lax"
    )

    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer"
    }


# User endpoints
@app.get(
    "/users/me",
    response_model=schemas.User,
    description="""## Get current user info"""
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get(
    "/users/me/accounts",
    response_model=List[schemas.Account],
    description="""## Get accounts of current user"""
)
async def read_user_accounts(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await get_user_accounts(db, user_id=current_user.id)


@app.get(
    "/users/me/payments",
    response_model=List[schemas.Payment],
    description="""## Get payments of current user"""
)
async def read_user_payments(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await get_user_payments(db, user_id=current_user.id)


# Admin endpoints
@app.get(
    "/admin/users",
    response_model=List[schemas.UserWithAccounts],
    description="""## Get users with accounts info"""
)
async def read_users(
        skip: int = 0, limit: int = 100,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    return await get_users_with_accounts(db, skip=skip, limit=limit)


@app.post("/admin/users", response_model=schemas.User)
async def create_user(
        user: schemas.UserCreate,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return await crud_create_user(db=db, user=user)


@app.put("/admin/users/{user_id}", response_model=schemas.User)
async def update_user(
        user_id: int,
        user: schemas.UserUpdate,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    db_user = await get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return await crud_update_user(db=db, user_id=user_id, user=user)


@app.delete("/admin/users/{user_id}", response_model=schemas.User)
async def delete_user(
        user_id: int,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    db_user = await get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud_delete_user(db=db, user_id=user_id)


# Payment webhook
@app.post("/webhook/payment", response_model=schemas.PaymentResponse)
async def process_payment_webhook(
        payment: schemas.PaymentWebhook,
        db: AsyncSession = Depends(get_db)
):
    calculated_signature = await calculate_payment_signature(payment)
    await logger.info(
        f"Received payment webhook: {payment.model_dump()}"
    )
    if calculated_signature != payment.signature:
        await logger.warning(
            f"Invalid signature for transaction,"
            f"expected: {calculated_signature}, got: {payment.signature}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    # Check if transaction already exists
    existing_payment = await get_payment_by_transaction_id(
        db,
        transaction_id=payment.transaction_id
    )
    if existing_payment:
        await logger.warning(
            f"Duplicate transaction: {payment.transaction_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction already processed"
        )

    # Check if user exists
    user = await get_user(db, user_id=payment.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if account exists, create if not
    account = await get_account(db, account_id=payment.account_id)
    if not account:
        await create_account(
            db,
            account_id=payment.account_id,
            user_id=payment.user_id
        )

    # Create payment and update account balance
    payment_db = await create_payment(
        db,
        transaction_id=payment.transaction_id,
        account_id=payment.account_id,
        user_id=payment.user_id,
        amount=payment.amount
    )

    # Update account balance
    await update_account_balance(
        db,
        account_id=payment.account_id,
        amount=payment.amount
    )

    await logger.info(
        f"Processed transaction: {payment.transaction_id}, "
        f"amount={payment.amount}, "
        f"account={payment.account_id}"
    )
    return {
        "status": "success",
        "message": "Payment processed successfully",
        "payment_id": payment_db.id
    }
