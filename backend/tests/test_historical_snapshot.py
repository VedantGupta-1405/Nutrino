"""
Dedicated tests for historical nutrition snapshot immutability.
Verifies that modifying a FoodItem's nutritional values later does NOT alter previously logged MealItem records.
"""

from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.food import FoodItem
from app.models.meal import MealItem


def register_user(client: TestClient, prefix: str = "snapuser") -> tuple[str, dict]:
    """Helper to register a user and return Bearer token and user dictionary."""
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Snapshot Tester", "email": email, "password": "Password123!"},
    )
    assert res.status_code == 201
    data = res.json()
    return data["access_token"], data["user"]


def test_historical_meal_item_snapshot_immutability(client: TestClient, db_session: Session):
    """
    Step 1: Create a food item with initial nutrition values (100 kcal, 5g protein).
    Step 2: User logs a meal with 2 servings (expected 200 kcal, 10g protein).
    Step 3: Modify the food item in the catalog (change to 150 kcal, 8g protein).
    Step 4: Fetch original meal and verify MealItem still has 200 kcal and 10g protein.
    """
    token, _ = register_user(client, "snapshot")

    # Step 1: Create a dynamic food item
    food = FoodItem(
        name=f"Custom Bar {uuid.uuid4().hex[:6]}",
        category="SNACK",
        serving_size=Decimal("1.00"),
        serving_unit="piece",
        calories=Decimal("100.00"),
        protein=Decimal("5.00"),
        carbohydrates=Decimal("15.00"),
        fat=Decimal("2.00"),
        fiber=Decimal("1.00"),
        source="TEST_DATASET",
    )
    db_session.add(food)
    db_session.commit()
    db_session.refresh(food)

    try:
        # Step 2: User logs 2 pieces
        log_res = client.post(
            "/api/v1/meals",
            json={"meal_type": "SNACK", "items": [{"food_id": food.id, "quantity": 2, "unit": "piece"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert log_res.status_code == 201
        meal_data = log_res.json()
        meal_id = meal_data["id"]

        assert float(meal_data["totals"]["calories"]) == 200.0
        assert float(meal_data["totals"]["protein"]) == 10.0

        # Step 3: Modify the FoodItem catalog record (e.g. manufacturer reformulated recipe)
        food.calories = Decimal("150.00")
        food.protein = Decimal("8.00")
        db_session.commit()

        # Step 4: Retrieve the original meal via API
        get_res = client.get(f"/api/v1/meals/{meal_id}", headers={"Authorization": f"Bearer {token}"})
        assert get_res.status_code == 200
        retrieved_meal = get_res.json()

        # Step 5: Verify the historical MealItem snapshot is PRESERVED and NOT altered by the FoodItem change
        assert float(retrieved_meal["totals"]["calories"]) == 200.0
        assert float(retrieved_meal["totals"]["protein"]) == 10.0

        retrieved_item = retrieved_meal["items"][0]
        assert float(retrieved_item["calculated_calories"]) == 200.0
        assert float(retrieved_item["calculated_protein"]) == 10.0

        # Verify directly on the MealItem database row
        db_item = db_session.query(MealItem).filter(MealItem.meal_id == meal_id).first()
        assert db_item is not None
        assert db_item.calculated_calories == Decimal("200.00")
        assert db_item.calculated_protein == Decimal("10.00")
    finally:
        # Clean up meal first (which cascades to meal_items), then clean up the test food item
        if "meal_id" in locals():
            client.delete(f"/api/v1/meals/{meal_id}", headers={"Authorization": f"Bearer {token}"})
        db_session.delete(food)
        db_session.commit()

