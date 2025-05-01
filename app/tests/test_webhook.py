import hashlib

import pytest

from app import crud
from app.config import settings


@pytest.mark.asyncio
async def test_process_payment_webhook(
        async_client,
        db_session,
        test_user,
        test_account
):
    # Create webhook payload
    transaction_id = "test-transaction-webhook-123"
    account_id = test_account.id
    user_id = test_user.id
    amount = 75.0

    # Calculate signature
    data_string = (f"{account_id}{str(int(amount))}{transaction_id}"
                   f"{user_id}{settings.WEBHOOK_SECRET_KEY}")
    signature = hashlib.sha256(data_string.encode()).hexdigest()

    payload = {
        "transaction_id": transaction_id,
        "account_id": account_id,
        "user_id": user_id,
        "amount": amount,
        "signature": signature
    }

    # Initial balance
    initial_balance = test_account.balance

    # Send webhook request
    response = await async_client.post(
        "/webhook/payment",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Payment processed successfully"
    assert "payment_id" in data

    # Verify payment was created
    payment = await crud.get_payment_by_transaction_id(
        db=db_session,
        transaction_id=transaction_id
    )
    assert payment is not None
    assert payment.transaction_id == transaction_id
    assert payment.amount == amount

    # Verify account balance was updated
    updated_account = await crud.get_account(db=db_session,
                                             account_id=account_id)
    assert updated_account.balance == initial_balance + amount


@pytest.mark.asyncio
async def test_process_payment_webhook_invalid_signature(
        async_client,
        test_user,
        test_account
):
    # Create webhook payload with invalid signature
    payload = {
        "transaction_id": "test-transaction-invalid-sig",
        "account_id": test_account.id,
        "user_id": test_user.id,
        "amount": 50.0,
        "signature": "invalid-signature"
    }

    # Send webhook request
    response = await async_client.post(
        "/webhook/payment",
        json=payload
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"


@pytest.mark.asyncio
async def test_process_payment_webhook_duplicate_transaction(
        async_client,
        db_session,
        test_user,
        test_account
):
    # Create webhook payload
    transaction_id = "test-transaction-duplicate"
    account_id = test_account.id
    user_id = test_user.id
    amount = 25.0

    # Calculate signature
    data_string = (f"{account_id}{str(int(amount))}{transaction_id}"
                   f"{user_id}{settings.WEBHOOK_SECRET_KEY}")
    signature = hashlib.sha256(data_string.encode()).hexdigest()

    payload = {
        "transaction_id": transaction_id,
        "account_id": account_id,
        "user_id": user_id,
        "amount": amount,
        "signature": signature
    }

    # Create payment first
    payment = await crud.create_payment(
        db=db_session,
        transaction_id=transaction_id,
        account_id=account_id,
        user_id=user_id,
        amount=amount
    )

    # Send webhook request with same transaction_id
    response = await async_client.post(
        "/webhook/payment",
        json=payload
    )
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "Transaction already processed"


@pytest.mark.asyncio
async def test_process_payment_webhook_nonexistent_user(
        async_client,
        test_account
):
    # Create webhook payload with non-existent user
    transaction_id = "test-transaction-no-user"
    account_id = test_account.id
    user_id = 9999  # Non-existent user ID
    amount = 30.0

    # Calculate signature
    data_string = (f"{account_id}{str(int(amount))}{transaction_id}"
                   f"{user_id}{settings.WEBHOOK_SECRET_KEY}")
    signature = hashlib.sha256(data_string.encode()).hexdigest()

    payload = {
        "transaction_id": transaction_id,
        "account_id": account_id,
        "user_id": user_id,
        "amount": amount,
        "signature": signature
    }

    # Send webhook request
    response = await async_client.post(
        "/webhook/payment",
        json=payload
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_process_payment_webhook_create_account(
        async_client,
        db_session,
        test_user
):
    # Create webhook payload with new account ID
    transaction_id = "test-transaction-new-account"
    account_id = 9999  # New account ID
    user_id = test_user.id
    amount = 40.0

    # Calculate signature
    data_string = (f"{account_id}{str(int(amount))}{transaction_id}"
                   f"{user_id}{settings.WEBHOOK_SECRET_KEY}")
    signature = hashlib.sha256(data_string.encode()).hexdigest()

    payload = {
        "transaction_id": transaction_id,
        "account_id": account_id,
        "user_id": user_id,
        "amount": amount,
        "signature": signature
    }

    # Verify account doesn't exist yet
    account_before = await crud.get_account(db=db_session,
                                            account_id=account_id)
    assert account_before is None

    # Send webhook request
    response = await async_client.post(
        "/webhook/payment",
        json=payload
    )
    assert response.status_code == 200

    # Verify account was created
    account_after = await crud.get_account(db=db_session,
                                           account_id=account_id)
    assert account_after is not None
    assert account_after.id == account_id
    assert account_after.user_id == user_id
    assert account_after.balance == amount
