import pytest

from app import models


@pytest.mark.asyncio
async def test_user_model(db_session):
    # Create a user
    user = models.User(
        email="modeltest@example.com",
        hashed_password="hashed_password",
        full_name="Model Test User",
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Verify user was created
    assert user.id is not None
    assert user.email == "modeltest@example.com"
    assert user.full_name == "Model Test User"
    assert user.is_admin is False

    # Test relationships
    assert hasattr(user, "accounts")
    assert hasattr(user, "payments")


@pytest.mark.asyncio
async def test_account_model(db_session):
    # Create a user first
    user = models.User(
        email="accounttest@example.com",
        hashed_password="hashed_password",
        full_name="Account Test User",
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()

    # Create an account
    account = models.Account(
        id=1000,
        user_id=user.id,
        balance=150.0
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    # Verify account was created
    assert account.id == 1000
    assert account.user_id == user.id
    assert account.balance == 150.0

    # Test relationships
    assert hasattr(account, "owner")
    assert hasattr(account, "payments")

    # Test back-reference
    await db_session.refresh(user)
    assert len(user.accounts) == 1
    assert user.accounts[0].id == account.id


@pytest.mark.asyncio
async def test_payment_model(db_session):
    # Create a user first
    user = models.User(
        email="paymenttest@example.com",
        hashed_password="hashed_password",
        full_name="Payment Test User",
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()

    # Create an account
    account = models.Account(
        id=2000,
        user_id=user.id,
        balance=200.0
    )
    db_session.add(account)
    await db_session.commit()

    # Create a payment
    payment = models.Payment(
        transaction_id="test-transaction-model",
        account_id=account.id,
        user_id=user.id,
        amount=75.0
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    # Verify payment was created
    assert payment.id is not None
    assert payment.transaction_id == "test-transaction-model"
    assert payment.account_id == account.id
    assert payment.user_id == user.id
    assert payment.amount == 75.0
    assert payment.created_at is not None

    # Test relationships
    assert hasattr(payment, "account")
    assert hasattr(payment, "user")

    # Test back-references
    await db_session.refresh(account)
    await db_session.refresh(user)
    assert len(account.payments) == 1
    assert account.payments[0].id == payment.id
    assert len(user.payments) == 1
    assert user.payments[0].id == payment.id
