"""
Unit and integration tests for Goal endpoints and services (Phase 3).
Covers goal creation, retrieval, updates, validation, authentication, and user isolation.
"""

import uuid
from fastapi.testclient import TestClient


def register_user(client: TestClient, prefix: str = "goal") -> tuple[str, dict]:
    """Helper to register a user and return the Bearer token and user dictionary."""
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Goal Tester", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201
    data = res.json()
    return data["access_token"], data["user"]


def test_get_goal_not_found_before_creation(client: TestClient):
    """Test GET /api/v1/goals returns 404 if goal has not been set yet."""
    token, _ = register_user(client, "nogoral")
    res = client.get("/api/v1/goals", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_and_retrieve_goal(client: TestClient):
    """Test creating a goal via PUT and retrieving it via GET."""
    token, user = register_user(client, "creategoal")
    goal_payload = {
        "goal_type": "WEIGHT_MANAGEMENT",
        "target_calories": 2100.0,
        "target_protein": 140.0,
        "target_carbohydrates": 220.0,
        "target_fat": 65.0,
        "notes": "Targeting steady fat loss while preserving muscle",
    }

    # PUT creates the goal
    put_res = client.put(
        "/api/v1/goals",
        json=goal_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_res.status_code == 200
    data = put_res.json()

    assert data["user_id"] == user["id"]
    assert data["goal_type"] == "WEIGHT_MANAGEMENT"
    assert data["target_calories"] == 2100.0
    assert data["target_protein"] == 140.0
    assert data["target_carbohydrates"] == 220.0
    assert data["target_fat"] == 65.0
    assert data["is_active"] is True
    assert data["notes"] == "Targeting steady fat loss while preserving muscle"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # GET retrieves the same active goal
    get_res = client.get(
        "/api/v1/goals",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json() == data


def test_valid_goal_types(client: TestClient):
    """Verify that all supported goal types are accepted."""
    token, _ = register_user(client, "types")
    valid_types = ["WEIGHT_MANAGEMENT", "MUSCLE_GAIN", "GENERAL_HEALTH"]

    for g_type in valid_types:
        res = client.put(
            "/api/v1/goals",
            json={"goal_type": g_type, "target_calories": 2000.0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["goal_type"] == g_type


def test_invalid_goal_type(client: TestClient):
    """Verify that unsupported goal types are rejected with 422."""
    token, _ = register_user(client, "badtype")
    res = client.put(
        "/api/v1/goals",
        json={"goal_type": "EXTREME_STARVATION_FAD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422
    assert "error" in res.json()


def test_invalid_target_values(client: TestClient):
    """Verify validation on impossible or negative nutrition target values."""
    token, _ = register_user(client, "badvals")

    # Negative calories
    res1 = client.put(
        "/api/v1/goals",
        json={"goal_type": "MUSCLE_GAIN", "target_calories": -500.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 422

    # Impossible calories (> 10000)
    res2 = client.put(
        "/api/v1/goals",
        json={"goal_type": "MUSCLE_GAIN", "target_calories": 15000.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 422

    # Negative protein
    res3 = client.put(
        "/api/v1/goals",
        json={"goal_type": "MUSCLE_GAIN", "target_protein": -50.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res3.status_code == 422

    # Negative fat
    res4 = client.put(
        "/api/v1/goals",
        json={"goal_type": "MUSCLE_GAIN", "target_fat": -20.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res4.status_code == 422


def test_goal_unauthenticated(client: TestClient):
    """Test unauthenticated requests to goal endpoints return 401."""
    get_res = client.get("/api/v1/goals")
    assert get_res.status_code == 401
    assert get_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"

    put_res = client.put("/api/v1/goals", json={"goal_type": "GENERAL_HEALTH"})
    assert put_res.status_code == 401
    assert put_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_goal_user_isolation(client: TestClient):
    """Verify that User A and User B maintain completely isolated goals."""
    token_a, user_a = register_user(client, "goala")
    token_b, user_b = register_user(client, "goalb")

    # User A sets goal
    client.put(
        "/api/v1/goals",
        json={"goal_type": "MUSCLE_GAIN", "target_protein": 180.0, "target_calories": 2800.0},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B sets goal
    client.put(
        "/api/v1/goals",
        json={"goal_type": "WEIGHT_MANAGEMENT", "target_protein": 110.0, "target_calories": 1600.0},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A retrieves goal: gets User A's data
    res_a = client.get("/api/v1/goals", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    assert res_a.json()["user_id"] == user_a["id"]
    assert res_a.json()["goal_type"] == "MUSCLE_GAIN"
    assert res_a.json()["target_protein"] == 180.0

    # User B retrieves goal: gets User B's data
    res_b = client.get("/api/v1/goals", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["user_id"] == user_b["id"]
    assert res_b.json()["goal_type"] == "WEIGHT_MANAGEMENT"
    assert res_b.json()["target_protein"] == 110.0
