"""Pytest configuration, shared fixtures for SoloMiro backend tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.services.ai_service import MockAIProvider
from app.services.recommender import CarRecommender
from config.settings import Settings

# ---------------------------------------------------------------------------
# Settings fixture (SQLite in-memory, no real AI key)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Return a Settings instance pointing to an in-memory SQLite database."""
    s = Settings()
    s.DATABASE_URL = "sqlite:///:memory:"
    s.AI_PROVIDER = "anthropic"
    s.AI_API_KEY = "test_key"
    return s


# ---------------------------------------------------------------------------
# In-memory database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh SQLite in-memory engine per test function.

    Uses a shared in-memory URL so both the engine and any session created
    from it see the same database within the same process.
    """
    engine = create_engine(
        "sqlite:///file:testdb?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Yield a database session bound to the in-memory engine."""
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# TestClient fixture with DB override
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def client(db_engine):
    """Return a FastAPI TestClient with an overridden in-memory DB dependency.

    Patches app.database.init_db to a no-op so the lifespan does not create
    a second engine pointing at the on-disk SQLite path.
    """
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Override the recommender dependency to use MockAIProvider
    from app.routers.advisor import _get_recommender
    from config.settings import settings as app_settings

    def override_recommender():
        return CarRecommender(ai_provider=MockAIProvider(), settings=app_settings)

    app.dependency_overrides[_get_recommender] = override_recommender

    # Patch init_db so the lifespan does not touch a different engine/file
    with patch("app.main.init_db", return_value=None):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Recommender fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ai() -> MockAIProvider:
    """Return a MockAIProvider instance."""
    return MockAIProvider()


@pytest.fixture
def recommender(mock_ai, test_settings) -> CarRecommender:
    """Return a CarRecommender using MockAIProvider and test settings."""
    return CarRecommender(ai_provider=mock_ai, settings=test_settings)
