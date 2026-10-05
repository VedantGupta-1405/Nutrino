"""
Unit and API integration tests for Meal creation, retrieval, deletion, atomicity, and user isolation (Phase 5).
"""

from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.food import FoodItem
from app.models.meal import Meal, MealItem
from app.database.seed import seed_foods
from app.services.food_service import food_service


def register_user(client: TestClient, prefix: str = "mealuser") -> tuple[str, dict]:
    """Helper to register a user and return Bearer token and user dictionary."""
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Meal Tester", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201
    data = res.json()
    return data["access_token"], data["user"]


def test_create_meal_single_item(client: TestClient, db_session: Session):
    """Test creating a meal with a single food item."""
    seed_foods(db_session)
    token, user = register_user(client, "single")
    idli = food_service.get_by_name(db_session, "Idli")
    assert idli is not None

    payload = {
        "meal_type": "BREAKFAST",
        "items": [
            {"food_id": idli.id, "quantity": 2, "unit": "piece"}
        ],
    }

    res = client.post("/api/v1/meals", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    data = res.json()

    assert data["user_id"] == user["id"]
    assert data["meal_type"] == "BREAKFAST"
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["food_item_id"] == idli.id
    assert item["food_name"] == "Idli"
    assert float(item["quantity"]) == 2.0
    # 58 kcal * 2 = 116 kcal
    assert float(item["calculated_calories"]) == 116.0
    # 1.6g protein * 2 = 3.2g
    assert float(item["calculated_protein"]) == 3.2

    # Verify totals
    assert float(data["totals"]["calories"]) == 116.0
    assert float(data["totals"]["protein"]) == 3.2


def test_create_meal_multiple_items(client: TestClient, db_session: Session):
    """Test creating a meal with multiple food items and verifying exact nutritional summation."""
    seed_foods(db_session)
    token, _ = register_user(client, "multi")
    dosa = food_service.get_by_name(db_session, "Plain Dosa")
    sambar = food_service.get_by_name(db_session, "Sambar")
    coffee = food_service.get_by_name(db_session, "Filter Coffee with Milk")

    payload = {
        "meal_type": "BREAKFAST",
        "items": [
            {"food_id": dosa.id, "quantity": 2, "unit": "piece"},          # 133*2 = 266 kcal, 2.7*2 = 5.4g P
            {"food_id": sambar.id, "quantity": 150, "unit": "ml"},          # 120 kcal, 4.5g P
            {"food_id": coffee.id, "quantity": 1, "unit": "cup"},           # 75 kcal, 2.5g P
        ],
    }

    res = client.post("/api/v1/meals", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    data = res.json()

    assert len(data["items"]) == 3
    # Expected calories: 266 + 120 + 75 = 461 kcal
    assert float(data["totals"]["calories"]) == 461.0
    # Expected protein: 5.4 + 4.5 + 2.5 = 12.4g
    assert float(data["totals"]["protein"]) == 12.4


def test_create_meal_invalid_food_id(client: TestClient):
    """Test logging a meal with a non-existent FoodItem ID returns 404."""
    token, _ = register_user(client, "badfood")
    payload = {
        "meal_type": "LUNCH",
        "items": [{"food_id": 999999, "quantity": 1, "unit": "serving"}],
    }
    res = client.post("/api/v1/meals", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_meal_invalid_quantity(client: TestClient, db_session: Session):
    """Test logging a meal with zero or negative quantity is rejected with 422."""
    seed_foods(db_session)
    token, _ = register_user(client, "badqty")
    idli = food_service.get_by_name(db_session, "Idli")

    payload = {
        "meal_type": "DINNER",
        "items": [{"food_id": idli.id, "quantity": -2, "unit": "piece"}],
    }
    res = client.post("/api/v1/meals", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422


def test_create_meal_incompatible_unit(client: TestClient, db_session: Session):
    """Test unit incompatibility (e.g. requesting grams for piece-based dosa) fails validation."""
    seed_foods(db_session)
    token, _ = register_user(client, "badunit")
    dosa = food_service.get_by_name(db_session, "Plain Dosa")

    payload = {
        "meal_type": "BREAKFAST",
        "items": [{"food_id": dosa.id, "quantity": 100, "unit": "gram"}],
    }
    res = client.post("/api/v1/meals", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422
    assert "Cannot convert" in res.json()["error"]["message"]


def test_meal_creation_atomic_rollback(client: TestClient, db_session: Session):
    """Verify that if one item in a multi-item meal fails, no records are persisted in the database."""
    seed_foods(db_session)
    token, user = register_user(client, "rollback")
    idli = food_service.get_by_name(db_session, "Idli")
    dosa = food_service.get_by_name(db_session, "Plain Dosa")

    initial_meal_count = db_session.query(Meal).filter(Meal.user_id == user["id"]).count()
    initial_item_count = db_session.query(MealItem).count()

    # Second item has incompatible unit (gram for dosa)
    payload = {
        "meal_type": "BREAKFAST",
        "items": [
            {"food_id": idli.id, "quantity": 2, "unit": "piece"},      # valid
            {"food_id": dosa.id, "quantity": 100, "unit": "gram"},     # invalid unit!
        ],
    }

    res = client.post("/api/v1/meals", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422

    # Verify atomic rollback: zero meals or items added
    final_meal_count = db_session.query(Meal).filter(Meal.user_id == user["id"]).count()
    final_item_count = db_session.query(MealItem).count()
    assert final_meal_count == initial_meal_count
    assert final_item_count == initial_item_count


def test_get_meal_by_id(client: TestClient, db_session: Session):
    """Test retrieving a logged meal by its primary key ID."""
    seed_foods(db_session)
    token, user = register_user(client, "getbyid")
    rice = food_service.get_by_name(db_session, "Cooked White Rice")

    create_res = client.post(
        "/api/v1/meals",
        json={"meal_type": "LUNCH", "items": [{"food_id": rice.id, "quantity": 150, "unit": "gram"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    meal_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/meals/{meal_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 200
    assert get_res.json()["id"] == meal_id
    assert get_res.json()["meal_type"] == "LUNCH"


def test_list_and_today_meals(client: TestClient, db_session: Session):
    """Test listing user meals and fetching today's meals."""
    seed_foods(db_session)
    token, _ = register_user(client, "today")
    idli = food_service.get_by_name(db_session, "Idli")

    client.post(
        "/api/v1/meals",
        json={"meal_type": "BREAKFAST", "items": [{"food_id": idli.id, "quantity": 2, "unit": "piece"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    # GET /api/v1/meals
    list_res = client.get("/api/v1/meals", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # GET /api/v1/meals/today
    today_res = client.get("/api/v1/meals/today", headers={"Authorization": f"Bearer {token}"})
    assert today_res.status_code == 200
    assert len(today_res.json()) >= 1


def test_delete_meal(client: TestClient, db_session: Session):
    """Test deleting a meal cascades and deletes its MealItems."""
    seed_foods(db_session)
    token, _ = register_user(client, "delmeal")
    dosa = food_service.get_by_name(db_session, "Plain Dosa")

    create_res = client.post(
        "/api/v1/meals",
        json={"meal_type": "BREAKFAST", "items": [{"food_id": dosa.id, "quantity": 1, "unit": "piece"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    meal_id = create_res.json()["id"]

    # Delete meal
    del_res = client.delete(f"/api/v1/meals/{meal_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/meals/{meal_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 404

    # Verify in DB that items were cascaded and removed
    item_count = db_session.query(MealItem).filter(MealItem.meal_id == meal_id).count()
    assert item_count == 0


def test_meal_user_isolation(client: TestClient, db_session: Session):
    """Verify that User A cannot view or delete User B's meals."""
    seed_foods(db_session)
    token_a, _ = register_user(client, "userameal")
    token_b, _ = register_user(client, "userbmeal")
    idli = food_service.get_by_name(db_session, "Idli")

    # User A creates meal
    res_a = client.post(
        "/api/v1/meals",
        json={"meal_type": "BREAKFAST", "items": [{"food_id": idli.id, "quantity": 2, "unit": "piece"}]},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    meal_id_a = res_a.json()["id"]

    # User B attempts to GET User A's meal -> returns 404 (does not leak existence)
    res_b_get = client.get(f"/api/v1/meals/{meal_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_get.status_code == 404

    # User B attempts to DELETE User A's meal -> returns 404
    res_b_del = client.delete(f"/api/v1/meals/{meal_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_del.status_code == 404

    # User A can still retrieve their meal safely
    res_a_check = client.get(f"/api/v1/meals/{meal_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_check.status_code == 200
