"""
Shared pytest fixtures for Nutrino backend test suite.
"""

import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "llm: mark tests that require live Ollama LLM execution")


from app.main import app
from app.database.session import SessionLocal


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture for FastAPI endpoints."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provides a transactional database session for unit/integration tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
