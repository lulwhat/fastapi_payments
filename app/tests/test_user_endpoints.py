import pytest
from app import crud


@pytest.mark.asyncio
async def test_read_users_me(async_client, test_user, user_token):
    response = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_read_users_me_unauthorized(async_client):
    response = await async_client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_read_user_accounts(
        async_client,
        test_user,
        test_account,
        user_token: str
):
    response = await async_client.get(
        "/users/me/accounts",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_account.id
    assert data[0]["balance"] == test_account.balance
    assert data[0]["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_read_user_payments(
        async_client,
        db_session,
        test_user,
        test_account,
        user_token: str
):
    # Create a test payment
    payment = await crud.create_payment(
        db=db_session,
        transaction_id="test-transaction-123",
        account_id=test_account.id,
        user_id=test_user.id,
        amount=50.0
    )

    response = await async_client.get(
        "/users/me/payments",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == payment.id
    assert data[0]["transaction_id"] == payment.transaction_id
    assert data[0]["amount"] == payment.amount
