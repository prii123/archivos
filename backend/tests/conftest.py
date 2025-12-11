import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db import Base, get_db
from app.models import RoleEnum
from app import crud

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/docmanager_test"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """Create a clean database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session):
    """Create a test client with overridden database session."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session):
    """Create a test user."""
    user = await crud.create_user(
        db_session,
        email="test@example.com",
        password="testpass123",
        role=RoleEnum.USER
    )
    return user


@pytest.fixture(scope="function")
async def test_admin_user(db_session):
    """Create a test admin user."""
    admin_user = await crud.create_user(
        db_session,
        email="admin@example.com",
        password="adminpass123",
        role=RoleEnum.ADMIN
    )
    return admin_user


@pytest.fixture(scope="function")
async def test_superadmin_user(db_session):
    """Create a test superadmin user."""
    superadmin = await crud.create_user(
        db_session,
        email="superadmin@example.com",
        password="superpass123",
        role=RoleEnum.SUPERADMIN
    )
    return superadmin


@pytest.fixture(scope="function")
async def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
async def admin_auth_headers(client, test_admin_user):
    """Get authentication headers for admin user."""
    response = await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
