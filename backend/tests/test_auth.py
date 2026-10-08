"""
Unit and integration tests for Authentication (Phase 2).
Covers registration, login, token verification, password security, and /me endpoint.
"""

from datetime import timedelta
import uuid
import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth.security import create_access_token, verify_password


def random_email(prefix: str = "user") -> str:
    """Generate a unique email address for test isolation."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def test_register_success(client: TestClient, db_session: Session):
    """Test successful user registration returns access token and safe user payload."""
    email = random_email("alex")
    payload = {
        "name": "Alex Nutrition",
        "email": email,
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert "user" in data

    user_data = data["user"]
    assert user_data["name"] == "Alex Nutrition"
    assert user_data["email"] == email.lower()
    assert user_data["is_active"] is True
    assert "id" in user_data
    assert "created_at" in user_data
    assert "updated_at" in user_data

    # Security requirement: password_hash must NEVER be returned
    assert "password_hash" not in user_data
    assert "password" not in user_data


def test_password_not_stored_in_plaintext(client: TestClient, db_session: Session):
    """Verify that password is stored as a secure bcrypt hash, not plaintext."""
    email = random_email("security")
    plain_password = "PlaintextPassword999!"
    payload = {
        "name": "Security Tester",
        "email": email,
        "password": plain_password,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    # Query the user directly from database
    user = db_session.query(User).filter(User.email == email.lower()).first()
    assert user is not None

    # Password must not be stored in plaintext
    assert user.password_hash != plain_password
    # Must be valid bcrypt hash starting with $2b$ or $2a$
    assert user.password_hash.startswith("$2")
    # Verify the hash matches using verify_password
    assert verify_password(plain_password, user.password_hash) is True


def test_register_duplicate_email(client: TestClient):
    """Test registering with an existing email returns 400 error."""
    email = random_email("dup")
    payload = {
        "name": "First User",
        "email": email,
        "password": "ValidPassword123!",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second attempt with same email (and different casing/whitespace)
    payload_dup = {
        "name": "Second User",
        "email": f"  {email.upper()}  ",
        "password": "AnotherPassword456!",
    }
    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 400
    error_data = res2.json()
    assert error_data["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_invalid_data(client: TestClient):
    """Test input validation for invalid email and short password."""
    # Invalid email format
    res1 = client.post(
        "/api/v1/auth/register",
        json={"name": "Test", "email": "not-an-email", "password": "ValidPassword123!"},
    )
    assert res1.status_code == 422

    # Password too short (< 8 chars)
    res2 = client.post(
        "/api/v1/auth/register",
        json={"name": "Test", "email": random_email("short"), "password": "short"},
    )
    assert res2.status_code == 422

    # Empty name
    res3 = client.post(
        "/api/v1/auth/register",
        json={"name": "", "email": random_email("empty"), "password": "ValidPassword123!"},
    )
    assert res3.status_code == 422


def test_login_success(client: TestClient):
    """Test successful login with registered credentials."""
    email = random_email("login")
    password = "CorrectPassword123!"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": email, "password": password},
    )

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email.lower()
    assert "password_hash" not in data["user"]


def test_login_wrong_password(client: TestClient):
    """Test login with incorrect password returns 401."""
    email = random_email("wrongpw")
    client.post(
        "/api/v1/auth/register",
        json={"name": "User", "email": email, "password": "RightPassword123!"},
    )

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "IncorrectPassword!"},
    )
    assert login_res.status_code == 401
    assert login_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_login_unknown_email(client: TestClient):
    """Test login with non-existent email returns 401."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": random_email("unknown"), "password": "SomePassword123!"},
    )
    assert login_res.status_code == 401
    assert login_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_me_authenticated_user(client: TestClient):
    """Test /api/v1/auth/me returns identity of authenticated user."""
    email = random_email("currentme")
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Current User", "email": email, "password": "ValidPassword123!"},
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == email.lower()
    assert data["name"] == "Current User"
    assert "password_hash" not in data


def test_me_missing_authorization_header(client: TestClient):
    """Test /api/v1/auth/me without Authorization header returns 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_me_invalid_jwt(client: TestClient):
    """Test /api/v1/auth/me with malformed JWT returns 401."""
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this-is-a-completely-invalid-jwt-token"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_me_expired_jwt(client: TestClient, db_session: Session):
    """Test /api/v1/auth/me with an expired JWT token returns 401."""
    email = random_email("expired")
    user = User(
        name="Expired User",
        email=email,
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Generate token expired 1 hour ago
    expired_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(hours=-1),
    )

    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_FAILED"
    assert "expired" in res.json()["error"]["message"].lower()


def test_me_tampered_signature_jwt(client: TestClient, db_session: Session):
    """Test /api/v1/auth/me with a JWT signed with a different key returns 401."""
    tampered_token = jwt.encode(
        {"sub": "9999", "exp": 9999999999},
        "wrong-secret-key-that-does-not-match-settings",
        algorithm="HS256",
    )

    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_inactive_user_cannot_access_me(client: TestClient, db_session: Session):
    """Test an inactive user account cannot authenticate or access /me."""
    email = random_email("inactive")
    inactive_user = User(
        name="Inactive User",
        email=email,
        password_hash="fakehash",
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()
    db_session.refresh(inactive_user)

    token = create_access_token(subject=inactive_user.id)
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    assert "inactive" in res.json()["error"]["message"].lower()


def test_single_user_session_endpoint(client: TestClient, db_session: Session):
    """Test obtaining personal single-user session token."""
    res = client.post("/api/v1/auth/session")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["is_active"] is True

    # Verify that the returned token can access /me
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["id"] == data["user"]["id"]

