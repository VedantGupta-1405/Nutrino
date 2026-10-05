"""
Unit and integration tests for UserProfile endpoints and services (Phase 3).
Covers creation, retrieval, updates, validation, authentication, and user isolation.
"""

import uuid
from fastapi.testclient import TestClient


def register_user(client: TestClient, prefix: str = "prof") -> tuple[str, dict]:
    """Helper to register a user and return the Bearer token and user dictionary."""
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201
    data = res.json()
    return data["access_token"], data["user"]


def test_get_profile_not_found_before_creation(client: TestClient):
    """Test GET /api/v1/profile returns 404 if profile has not been created yet."""
    token, _ = register_user(client, "noprof")
    res = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_and_retrieve_profile(client: TestClient):
    """Test creating a profile via PUT and retrieving it via GET."""
    token, user = register_user(client, "createprof")
    profile_data = {
        "age": 29,
        "height": 178.5,
        "weight": 74.0,
        "activity_level": "MODERATELY_ACTIVE",
        "dietary_preference": "VEGETARIAN",
        "preferred_cuisine": ["Indian", "Mediterranean", "  Indian  "],  # duplicate check
        "allergies_or_restrictions": ["peanuts", "lactose"],
        "disliked_foods": ["bitter gourd"],
        "budget_per_day": 350.0,
        "available_ingredients": ["rice", "toor dal", "tomatoes"],
    }

    # PUT creates profile idempotently
    put_res = client.put(
        "/api/v1/profile",
        json=profile_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_res.status_code == 200
    data = put_res.json()

    assert data["user_id"] == user["id"]
    assert data["age"] == 29
    assert data["height"] == 178.5
    assert data["weight"] == 74.0
    assert data["activity_level"] == "MODERATELY_ACTIVE"
    assert data["dietary_preference"] == "VEGETARIAN"
    assert data["preferred_cuisine"] == ["Indian", "Mediterranean"]  # sanitized and deduplicated
    assert data["allergies_or_restrictions"] == ["peanuts", "lactose"]
    assert data["disliked_foods"] == ["bitter gourd"]
    assert data["budget_per_day"] == 350.0
    assert data["available_ingredients"] == ["rice", "toor dal", "tomatoes"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # GET retrieves the exact same profile
    get_res = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json() == data


def test_partial_update_profile(client: TestClient):
    """Test updating existing profile fields while retaining previously stored information."""
    token, _ = register_user(client, "partprof")
    initial_data = {
        "age": 30,
        "height": 180.0,
        "weight": 85.0,
        "activity_level": "SEDENTARY",
        "dietary_preference": "NON_VEGETARIAN",
    }
    client.put("/api/v1/profile", json=initial_data, headers={"Authorization": f"Bearer {token}"})

    # Update only weight and activity_level
    update_data = {
        "weight": 82.5,
        "activity_level": "VERY_ACTIVE",
    }
    put_res = client.put(
        "/api/v1/profile",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["weight"] == 82.5
    assert updated["activity_level"] == "VERY_ACTIVE"
    assert updated["age"] == 30
    assert updated["height"] == 180.0
    assert updated["dietary_preference"] == "NON_VEGETARIAN"


def test_profile_validation_errors(client: TestClient):
    """Test validation constraints on age, height, weight, and budget."""
    token, _ = register_user(client, "valprof")

    # Negative age
    res1 = client.put("/api/v1/profile", json={"age": -1}, headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 422

    # Impossible age (> 120)
    res2 = client.put("/api/v1/profile", json={"age": 150}, headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 422

    # Negative height
    res3 = client.put("/api/v1/profile", json={"height": -170.0}, headers={"Authorization": f"Bearer {token}"})
    assert res3.status_code == 422

    # Negative weight
    res4 = client.put("/api/v1/profile", json={"weight": -60.0}, headers={"Authorization": f"Bearer {token}"})
    assert res4.status_code == 422

    # Negative budget
    res5 = client.put("/api/v1/profile", json={"budget_per_day": -100.0}, headers={"Authorization": f"Bearer {token}"})
    assert res5.status_code == 422


def test_profile_unauthenticated(client: TestClient):
    """Test unauthenticated requests to profile endpoints return 401."""
    get_res = client.get("/api/v1/profile")
    assert get_res.status_code == 401
    assert get_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"

    put_res = client.put("/api/v1/profile", json={"age": 25})
    assert put_res.status_code == 401
    assert put_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_profile_user_isolation(client: TestClient):
    """Verify that User A and User B maintain completely isolated profiles."""
    token_a, user_a = register_user(client, "usera")
    token_b, user_b = register_user(client, "userb")

    # User A creates profile
    client.put(
        "/api/v1/profile",
        json={"weight": 95.0, "dietary_preference": "VEGAN"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B creates profile
    client.put(
        "/api/v1/profile",
        json={"weight": 60.0, "dietary_preference": "NON_VEGETARIAN"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A reads profile: gets User A's data
    res_a = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    assert res_a.json()["user_id"] == user_a["id"]
    assert res_a.json()["weight"] == 95.0
    assert res_a.json()["dietary_preference"] == "VEGAN"

    # User B reads profile: gets User B's data
    res_b = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["user_id"] == user_b["id"]
    assert res_b.json()["weight"] == 60.0
    assert res_b.json()["dietary_preference"] == "NON_VEGETARIAN"
