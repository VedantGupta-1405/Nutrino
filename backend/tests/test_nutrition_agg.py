"""
Integration tests for daily nutrition aggregation, goal target comparisons, remaining macros, and history (Phase 5).
"""

from datetime import date, timedelta
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database.seed import seed_foods
from app.services.food_service import food_service


def register_user(client: TestClient, prefix: str = "nutruser") -> tuple[str, dict]:
    """Helper to register a user and return Bearer token and user dictionary."""
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Nutrition Tester", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201
    data = res.json()
    return data["access_token"], data["user"]


def test_daily_nutrition_zero_meals(client: TestClient):
    """Test requesting nutrition for a day with no meals returns zero totals rather than 404."""
    token, _ = register_user(client, "zeromeals")
    res = client.get("/api/v1/nutrition/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["meals_count"] == 0
    assert float(data["consumed"]["calories"]) == 0.0
    assert float(data["consumed"]["protein"]) == 0.0
    assert float(data["consumed"]["carbohydrates"]) == 0.0
    assert float(data["consumed"]["fat"]) == 0.0
    assert float(data["consumed"]["fiber"]) == 0.0
    assert data["target"] is None
    assert data["remaining"] is None


def test_daily_nutrition_with_meals(client: TestClient, db_session: Session):
    """Test daily aggregation correctly sums across multiple meals logged on the same date."""
    seed_foods(db_session)
    token, _ = register_user(client, "dailysum")
    idli = food_service.get_by_name(db_session, "Idli")            # 58 kcal, 1.6g P
    rice = food_service.get_by_name(db_session, "Cooked White Rice") # 130 kcal, 2.7g P

    # Meal 1: Breakfast (2 idlis) -> 116 kcal, 3.2g P
    client.post(
        "/api/v1/meals",
        json={"meal_type": "BREAKFAST", "items": [{"food_id": idli.id, "quantity": 2, "unit": "piece"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Meal 2: Lunch (200g rice) -> 260 kcal, 5.4g P
    client.post(
        "/api/v1/meals",
        json={"meal_type": "LUNCH", "items": [{"food_id": rice.id, "quantity": 200, "unit": "gram"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    res = client.get("/api/v1/nutrition/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["meals_count"] == 2
    # 116 + 260 = 376 kcal
    assert float(data["consumed"]["calories"]) == 376.0
    # 3.2 + 5.4 = 8.6g P
    assert float(data["consumed"]["protein"]) == 8.6


def test_daily_nutrition_with_active_goal(client: TestClient, db_session: Session):
    """Test daily nutrition computes remaining intake compared against the active user goal."""
    seed_foods(db_session)
    token, _ = register_user(client, "withgoal")
    chicken = food_service.get_by_name(db_session, "Cooked Chicken Breast") # 165 kcal, 31g P per 100g

    # Set user goal: 2000 kcal, 100g protein
    client.put(
        "/api/v1/goals",
        json={
            "goal_type": "MUSCLE_GAIN",
            "target_calories": 2000.0,
            "target_protein": 100.0,
            "target_carbohydrates": 250.0,
            "target_fat": 60.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Log 200g chicken -> 330 kcal, 62g protein
    client.post(
        "/api/v1/meals",
        json={"meal_type": "LUNCH", "items": [{"food_id": chicken.id, "quantity": 200, "unit": "gram"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    res = client.get("/api/v1/nutrition/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # Consumed
    assert float(data["consumed"]["calories"]) == 330.0
    assert float(data["consumed"]["protein"]) == 62.0

    # Target
    assert float(data["target"]["calories"]) == 2000.0
    assert float(data["target"]["protein"]) == 100.0

    # Remaining: max(target - consumed, 0)
    # 2000 - 330 = 1670 kcal
    assert float(data["remaining"]["calories"]) == 1670.0
    # 100 - 62 = 38g protein
    assert float(data["remaining"]["protein"]) == 38.0


def test_daily_nutrition_remaining_floors_at_zero(client: TestClient, db_session: Session):
    """Test that when consumption exceeds target, remaining macro values floor at zero (never negative)."""
    seed_foods(db_session)
    token, _ = register_user(client, "overtarget")
    paneer = food_service.get_by_name(db_session, "Paneer") # 265 kcal per 100g

    # Set low target: 500 kcal
    client.put(
        "/api/v1/goals",
        json={"goal_type": "WEIGHT_MANAGEMENT", "target_calories": 500.0, "target_protein": 20.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Log 300g paneer -> 795 kcal (exceeds 500 kcal target)
    client.post(
        "/api/v1/meals",
        json={"meal_type": "DINNER", "items": [{"food_id": paneer.id, "quantity": 300, "unit": "gram"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    res = client.get("/api/v1/nutrition/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert float(data["consumed"]["calories"]) == 795.0
    assert float(data["remaining"]["calories"]) == 0.0  # floored at zero!


def test_nutrition_history(client: TestClient):
    """Test querying nutritional history across a valid date range."""
    token, _ = register_user(client, "history")
    today = date.today()
    start_date = today - timedelta(days=6)

    res = client.get(
        f"/api/v1/nutrition/history?start_date={start_date.isoformat()}&end_date={today.isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["start_date"] == start_date.isoformat()
    assert data["end_date"] == today.isoformat()
    assert len(data["days"]) == 7


def test_nutrition_history_invalid_date_range(client: TestClient):
    """Test range validation: end before start, or range exceeding 31 days."""
    token, _ = register_user(client, "rangeval")
    today = date.today()

    # end_date before start_date
    res1 = client.get(
        f"/api/v1/nutrition/history?start_date={today.isoformat()}&end_date={(today - timedelta(days=2)).isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 422

    # span > 31 days
    res2 = client.get(
        f"/api/v1/nutrition/history?start_date={(today - timedelta(days=40)).isoformat()}&end_date={today.isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 422


def test_nutrition_user_isolation(client: TestClient, db_session: Session):
    """Verify that User A's meals do not alter User B's daily nutrition metrics."""
    seed_foods(db_session)
    token_a, _ = register_user(client, "usera_nutr")
    token_b, _ = register_user(client, "userb_nutr")
    idli = food_service.get_by_name(db_session, "Idli")

    # User A logs meal
    client.post(
        "/api/v1/meals",
        json={"meal_type": "BREAKFAST", "items": [{"food_id": idli.id, "quantity": 4, "unit": "piece"}]},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User A has 232 calories
    res_a = client.get("/api/v1/nutrition/today", headers={"Authorization": f"Bearer {token_a}"})
    assert float(res_a.json()["consumed"]["calories"]) == 232.0

    # User B still has 0 calories
    res_b = client.get("/api/v1/nutrition/today", headers={"Authorization": f"Bearer {token_b}"})
    assert float(res_b.json()["consumed"]["calories"]) == 0.0
    assert res_b.json()["meals_count"] == 0
