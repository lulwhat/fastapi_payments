import pytest
from app import models, crud, schemas


@pytest.mark.asyncio
async def test_read_users(
        async_client,
        test_user: models.User,
        test_admin: models.User,
        admin_token: str
):
    response = await async_client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least test_user and test_admin

    # Check if test_user is in the response
    user_found = False
    for user in data:
        if user["id"] == test_user.id:
            user_found = True
            assert user["email"] == test_user.email
            assert user["full_name"] == test_user.full_name
            break

    assert user_found, "Test user not found in response"


@pytest.mark.asyncio
async def test_read_users_unauthorized(async_client,
                                       user_token: str):
    response = await async_client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_create_user(async_client, admin_token: str):
    new_user_data = {
        "email": "newuser@example.com",
        "password": "newpassword",
        "full_name": "New User",
        "is_admin": False
    }

    response = await async_client.post(
        "/admin/users",
        json=new_user_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_user_data["email"]
    assert data["full_name"] == new_user_data["full_name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_update_user(
        async_client,
        test_user: models.User,
        admin_token: str
):
    update_data = {
        "full_name": "Updated User Name"
    }

    response = await async_client.put(
        f"/admin/users/{test_user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_delete_user(
        async_client,
        admin_token: str,
        db_session
):
    # Create a user to delete
    user_to_delete = await crud.crud_create_user(
        db=db_session,
        user=schemas.UserCreate(
            email="delete@example.com",
            password="deletepassword",
            full_name="Delete User",
            is_admin=False
        )
    )

    response = await async_client.delete(
        f"/admin/users/{user_to_delete.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_to_delete.id

    # Verify user is deleted
    deleted_user = await crud.get_user(db=db_session,
                                       user_id=user_to_delete.id)
    assert deleted_user is None
