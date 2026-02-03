import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import patch, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import UserRole
from app.security import create_access_token, get_password_hash

from datetime import datetime, date

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_celery_tasks():
    with patch("app.routes.bookings.process_booking_confirmation") as mock_task:
        mock_task.delay = MagicMock(return_value=None)
        yield mock_task


@pytest.fixture
async def test_host(db_session: AsyncSession):
    from app.models import User

    user = User(
        first_name="Host",
        last_name="User",
        email="host@example.com",
        password=get_password_hash("host123"),
        role=UserRole.HOST,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_customer(db_session: AsyncSession):
    from app.models import User

    user = User(
        first_name="Customer",
        last_name="User",
        email="customer@example.com",
        password=get_password_hash("customer123"),
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession):
    from app.models import User

    user = User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def host_token(test_host):
    return create_access_token({"sub": str(test_host.id)})


@pytest.fixture
async def customer_token(test_customer):
    return create_access_token({"sub": str(test_customer.id)})


@pytest.fixture
async def admin_token(test_admin):
    return create_access_token({"sub": str(test_admin.id)})


@pytest.fixture
async def test_property(db_session: AsyncSession, test_host):
    from app.models import Property

    property = Property(
        title="Test Property",
        description="This is a test property",
        address="New Address",
        price=100,
        city="Test City",
        beds=2,
        host_id=test_host.id,
    )
    db_session.add(property)
    await db_session.commit()
    await db_session.refresh(property)
    return property


@pytest.fixture
async def test_booking(db_session: AsyncSession, test_property, test_customer):
    from app.models import Booking

    booking = Booking(
        property_id=test_property.id,
        guest_id=test_customer.id,
        check_in=date(2025, 1, 1),
        check_out=date(2025, 1, 5),
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking
