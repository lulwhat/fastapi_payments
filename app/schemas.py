from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, ConfigDict


MODEL_CONFIG = ConfigDict(from_attributes=True, extra="forbid")


# Token schemas
class Token(BaseModel):
    status: str
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None


class User(UserBase):
    id: int
    is_admin: bool

    model_config = MODEL_CONFIG


# Account schemas
class AccountBase(BaseModel):
    id: int
    balance: float


class Account(AccountBase):
    user_id: int

    model_config = MODEL_CONFIG


# Payment schemas
class PaymentBase(BaseModel):
    transaction_id: str
    account_id: int
    user_id: int
    amount: float


class Payment(PaymentBase):
    id: int
    created_at: datetime

    model_config = MODEL_CONFIG


# Webhook schemas
class PaymentWebhook(BaseModel):
    transaction_id: str
    account_id: int
    user_id: int
    amount: float
    signature: str


class PaymentResponse(BaseModel):
    status: str
    message: str
    payment_id: int


# Combined schemas
class UserWithAccounts(User):
    accounts: List[Account] = []

    model_config = MODEL_CONFIG
