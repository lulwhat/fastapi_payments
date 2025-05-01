import os
from typing import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app import models, crud
from app import schemas
from app.base import Base
from app.database import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool
)

# Create test session
TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Test client fixture
@pytest_asyncio.fixture
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport,
                           base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Database session fixture
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session


# Test user fixture
@pytest_asyncio.fixture
async def test_user(db_session) -> models.User:
    user = await crud.crud_create_user(
        db=db_session,
        user=schemas.UserCreate(
            email="test@example.com",
            password="testpassword",
            full_name="Test User",
            is_admin=False
        )
    )
    return user


# Test admin fixture
@pytest_asyncio.fixture
async def test_admin(db_session) -> models.User:
    admin = await crud.crud_create_user(
        db=db_session,
        user=schemas.UserCreate(
            email="admin@example.com",
            password="adminpassword",
            full_name="Test Admin",
            is_admin=True
        )
    )
    return admin


# Test account fixture
@pytest_asyncio.fixture
async def test_account(db_session, test_user) -> models.Account:
    account = await crud.create_account(
        db=db_session,
        account_id=1,
        user_id=test_user.id,
        balance=100.0
    )
    return account


# Authentication token fixtures
@pytest_asyncio.fixture
async def user_token(async_client, test_user) -> str:
    response = await async_client.post(
        "/token",
        data={
            "username": test_user.email,
            "password": "testpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(async_client,
                      test_admin) -> str:
    response = await async_client.post(
        "/token",
        data={
            "username": test_admin.email,
            "password": "adminpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]
