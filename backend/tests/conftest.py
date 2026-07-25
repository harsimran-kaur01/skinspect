import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.main import app
from app.database import Base, get_db
from app.models.user import User

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up test database before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user."""

    def _create_user(
        email="test@example.com", password="TestPassword123", full_name="Test User"
    ):
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        return response

    return _create_user


@pytest.fixture
def auth_token(test_user):
    """Get an auth token for a test user."""
    response = test_user()
    return response.json()["token"]["access_token"]


@pytest.fixture
def auth_user(test_user):
    """Get the created test user object."""
    response = test_user()
    data = response.json()
    user = User(
        id=uuid.UUID(data["user"]["id"]),
        email=data["user"]["email"],
        full_name=data["user"]["full_name"],
        is_active=data["user"]["is_active"],
    )
    return user
