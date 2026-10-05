"""
Integration and API tests for FoodItem model, FoodService, seed data, and food endpoints.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.food import FoodItem
from app.database.seed import seed_foods
from app.services.food_service import food_service


@pytest.fixture(autouse=True)
def ensure_seed_data(db_session: Session):
    """Ensure baseline foods are populated before food tests execute."""
    seed_foods(db_session)


def test_seed_foods_idempotency(db_session: Session):
    """Verify that running the seed operation multiple times does not produce duplicate items."""
    count1 = seed_foods(db_session)
    assert count1 == 20

    count2 = seed_foods(db_session)
    assert count2 == 20

    total_rows = db_session.query(FoodItem).count()
    assert total_rows == 20


def test_database_check_constraints_negative_calories(db_session: Session):
    """Verify PostgreSQL check constraint rejects negative calories."""
    bad_food = FoodItem(
        name="Negative Calorie Food",
        category="OTHER",
        serving_size=Decimal("100.00"),
        serving_unit="gram",
        calories=Decimal("-10.00"),
        protein=Decimal("1.00"),
        carbohydrates=Decimal("1.00"),
        fat=Decimal("1.00"),
    )
    db_session.add(bad_food)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_check_constraints_negative_serving_size(db_session: Session):
    """Verify PostgreSQL check constraint rejects negative or zero serving size."""
    bad_food = FoodItem(
        name="Zero Serving Food",
        category="OTHER",
        serving_size=Decimal("0.00"),
        serving_unit="gram",
        calories=Decimal("100.00"),
        protein=Decimal("1.00"),
        carbohydrates=Decimal("1.00"),
        fat=Decimal("1.00"),
    )
    db_session.add(bad_food)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_food_service_search_exact_and_case_insensitive(db_session: Session):
    """Test searching by exact and case-insensitive names."""
    res1 = food_service.search(db_session, query="dosa")
    assert len(res1) >= 1
    assert any("dosa" in f.name.lower() for f in res1)

    res2 = food_service.search(db_session, query="PLAIN DOSA")
    assert len(res2) >= 1
    assert res2[0].name == "Plain Dosa"


def test_food_service_search_category_filter(db_session: Session):
    """Test searching with category filtering."""
    dairy_items = food_service.search(db_session, query="", category="DAIRY")
    assert len(dairy_items) == 0  # empty query returns empty list

    # Substring search filtered by category
    milk_items = food_service.search(db_session, query="milk", category="DAIRY")
    assert len(milk_items) >= 1
    for item in milk_items:
        assert item.category == "DAIRY"


def test_food_service_search_no_results(db_session: Session):
    """Test searching for non-existent food returns empty list."""
    res = food_service.search(db_session, query="nonexistentxyz123food")
    assert res == []


def test_food_service_search_pagination(db_session: Session):
    """Test pagination limit parameter."""
    res = food_service.search(db_session, query="a", limit=2)
    assert len(res) <= 2


def test_api_get_food_by_id_success(client: TestClient, db_session: Session):
    """Test GET /api/v1/foods/{food_id} returns food item data with decimal values."""
    food = food_service.get_by_name(db_session, "Idli")
    assert food is not None

    response = client.get(f"/api/v1/foods/{food.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == food.id
    assert data["name"] == "Idli"
    assert data["category"] == "GRAIN"
    assert data["serving_unit"] == "piece"
    assert float(data["calories"]) == 58.0
    assert float(data["protein"]) == 1.6
    assert data["source"] == "INTERNAL_DEV_DATASET"


def test_api_get_food_not_found(client: TestClient):
    """Test GET /api/v1/foods/{food_id} with non-existent ID returns 404."""
    response = client.get("/api/v1/foods/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_api_get_food_invalid_id_type(client: TestClient):
    """Test GET /api/v1/foods/abc returns 422 validation error."""
    response = client.get("/api/v1/foods/not-a-number")
    assert response.status_code == 422


def test_api_search_foods(client: TestClient):
    """Test GET /api/v1/foods/search returns matching list of foods."""
    response = client.get("/api/v1/foods/search?q=rice")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any("rice" in item["name"].lower() for item in data)


def test_api_search_foods_empty_query_rejected(client: TestClient):
    """Test GET /api/v1/foods/search with empty query is rejected by validation."""
    response = client.get("/api/v1/foods/search?q=")
    assert response.status_code == 422
