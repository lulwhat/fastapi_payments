from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, \
    DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_admin = Column(Boolean, default=False)

    accounts = relationship("Account", back_populates="owner",
                            lazy="selectin")
    payments = relationship("Payment", back_populates="user",
                            lazy="selectin")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float, default=0.0)

    owner = relationship("User", back_populates="accounts",
                         lazy="selectin")
    payments = relationship("Payment", back_populates="account",
                            lazy="selectin")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="payments",
                           lazy="selectin")
    user = relationship("User", back_populates="payments",
                        lazy="selectin")
