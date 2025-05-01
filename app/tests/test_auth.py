import pytest
from app import models


@pytest.mark.asyncio
async def test_login_success(async_client,
                             test_user):
    response = await async_client.post(
        "/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client, test_user):
    response = await async_client.post(
        "/token",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client):
    response = await async_client.post(
        "/token",
        data={
            "username": "nonexistent@example.com",
            "password": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
