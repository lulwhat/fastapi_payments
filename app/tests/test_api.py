import pytest
from app.schemas import PaymentWebhook


@pytest.mark.asyncio
async def test_auth_flow(async_client, test_admin):
    response = await async_client.post(
        "/token",
        data={"username": test_admin.email, "password": "adminpassword"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook(async_client, test_user, test_account, mock_logger):
    test_data = {
        "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
        "user_id": test_user.id,
        "account_id": test_account.id,
        "amount": 100,
        "signature": "7b47e41efe564a062029da3367bde"
                     "8844bea0fb049f894687cee5d57f2858bc8"
    }

    response = await async_client.post(
        "/webhook/payment",
        json=test_data
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
