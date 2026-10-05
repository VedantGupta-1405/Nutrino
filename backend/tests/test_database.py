"""
Tests for database engine, session management, and connectivity.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.session import check_db_connection, get_db


def test_check_db_connection():
    """Verify that check_db_connection returns healthy status and latency against live PostgreSQL."""
    result = check_db_connection()
    assert result["status"] == "healthy"
    assert result["database"] == "postgresql"
    assert "latency_ms" in result
    assert result["latency_ms"] > 0


def test_session_query(db_session: Session):
    """Verify that a session from the engine can execute raw and ORM queries."""
    result = db_session.execute(text("SELECT 42 AS answer")).scalar()
    assert result == 42


def test_get_db_generator():
    """Verify the FastAPI get_db dependency lifecycle."""
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)
    # verify query works on yielded session
    res = session.execute(text("SELECT 'nutrino' AS name")).scalar()
    assert res == "nutrino"
    # verify closing the generator closes the session without errors
    try:
        next(gen)
    except StopIteration:
        pass
