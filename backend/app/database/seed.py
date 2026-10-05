"""
Deterministic seed data script for internal food items catalog.
Idempotent: safe to execute repeatedly without duplicating food records.
All values are explicitly flagged with source="INTERNAL_DEV_DATASET" as developmental baseline data.
"""

from decimal import Decimal
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.schemas.food import FoodItemCreate
from app.services.food_service import food_service

logger = logging.getLogger(__name__)

INITIAL_FOODS: List[Dict[str, Any]] = [
    {
        "name": "Idli",
        "description": "Steamed savory fermented rice and black gram cake (approx. 40g)",
        "category": "GRAIN",
        "serving_size": Decimal("1.00"),
        "serving_unit": "piece",
        "calories": Decimal("58.00"),
        "protein": Decimal("1.60"),
        "carbohydrates": Decimal("12.00"),
        "fat": Decimal("0.20"),
        "fiber": Decimal("0.80"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Plain Dosa",
        "description": "Crispy fermented rice and lentil crepe prepared on griddle (approx. 80g)",
        "category": "GRAIN",
        "serving_size": Decimal("1.00"),
        "serving_unit": "piece",
        "calories": Decimal("133.00"),
        "protein": Decimal("2.70"),
        "carbohydrates": Decimal("18.80"),
        "fat": Decimal("5.20"),
        "fiber": Decimal("1.10"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Sambar",
        "description": "Lentil and mixed vegetable stew seasoned with tamarind and spices",
        "category": "LEGUME",
        "serving_size": Decimal("150.00"),
        "serving_unit": "ml",
        "calories": Decimal("120.00"),
        "protein": Decimal("4.50"),
        "carbohydrates": Decimal("18.00"),
        "fat": Decimal("3.20"),
        "fiber": Decimal("3.50"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Cooked White Rice",
        "description": "Boiled plain white basmati/polished rice",
        "category": "GRAIN",
        "serving_size": Decimal("100.00"),
        "serving_unit": "gram",
        "calories": Decimal("130.00"),
        "protein": Decimal("2.70"),
        "carbohydrates": Decimal("28.20"),
        "fat": Decimal("0.30"),
        "fiber": Decimal("0.40"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Cooked Toor Dal",
        "description": "Traditional yellow split pigeon pea curry tempered with cumin and mustard",
        "category": "LEGUME",
        "serving_size": Decimal("100.00"),
        "serving_unit": "gram",
        "calories": Decimal("116.00"),
        "protein": Decimal("7.30"),
        "carbohydrates": Decimal("17.50"),
        "fat": Decimal("2.10"),
        "fiber": Decimal("3.80"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Chapati",
        "description": "Whole wheat unleavened Indian flatbread cooked on tava (approx. 35g)",
        "category": "GRAIN",
        "serving_size": Decimal("1.00"),
        "serving_unit": "piece",
        "calories": Decimal("104.00"),
        "protein": Decimal("3.10"),
        "carbohydrates": Decimal("20.00"),
        "fat": Decimal("1.20"),
        "fiber": Decimal("3.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Paneer",
        "description": "Fresh non-aged, non-melting curd cheese made from cow/buffalo milk",
        "category": "DAIRY",
        "serving_size": Decimal("100.00"),
        "serving_unit": "gram",
        "calories": Decimal("265.00"),
        "protein": Decimal("18.30"),
        "carbohydrates": Decimal("3.40"),
        "fat": Decimal("20.80"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Curd",
        "description": "Traditional plain Indian fermented yogurt (dahi)",
        "category": "DAIRY",
        "serving_size": Decimal("100.00"),
        "serving_unit": "gram",
        "calories": Decimal("61.00"),
        "protein": Decimal("3.50"),
        "carbohydrates": Decimal("4.70"),
        "fat": Decimal("3.30"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Whole Milk",
        "description": "Pasteurized standardized whole dairy milk (approx. 1 glass/cup)",
        "category": "DAIRY",
        "serving_size": Decimal("250.00"),
        "serving_unit": "ml",
        "calories": Decimal("152.00"),
        "protein": Decimal("8.00"),
        "carbohydrates": Decimal("12.00"),
        "fat": Decimal("8.00"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Boiled Egg",
        "description": "Whole hard-boiled chicken egg (approx. 50g)",
        "category": "MEAT",
        "serving_size": Decimal("1.00"),
        "serving_unit": "piece",
        "calories": Decimal("78.00"),
        "protein": Decimal("6.30"),
        "carbohydrates": Decimal("0.60"),
        "fat": Decimal("5.30"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Cooked Chicken Breast",
        "description": "Boneless skinless chicken breast grilled or boiled",
        "category": "MEAT",
        "serving_size": Decimal("100.00"),
        "serving_unit": "gram",
        "calories": Decimal("165.00"),
        "protein": Decimal("31.00"),
        "carbohydrates": Decimal("0.00"),
        "fat": Decimal("3.60"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Cooked Mixed Vegetables",
        "description": "Steamed and lightly seasoned carrots, peas, beans, and cauliflower",
        "category": "VEGETABLE",
        "serving_size": Decimal("100.00"),
        "serving_unit": "gram",
        "calories": Decimal("65.00"),
        "protein": Decimal("2.20"),
        "carbohydrates": Decimal("11.00"),
        "fat": Decimal("1.50"),
        "fiber": Decimal("3.50"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Banana",
        "description": "Fresh ripe raw banana peeled (medium approx. 118g)",
        "category": "FRUIT",
        "serving_size": Decimal("1.00"),
        "serving_unit": "piece",
        "calories": Decimal("105.00"),
        "protein": Decimal("1.30"),
        "carbohydrates": Decimal("27.00"),
        "fat": Decimal("0.30"),
        "fiber": Decimal("3.10"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Apple",
        "description": "Fresh raw red/green apple with skin (medium approx. 182g)",
        "category": "FRUIT",
        "serving_size": Decimal("1.00"),
        "serving_unit": "piece",
        "calories": Decimal("95.00"),
        "protein": Decimal("0.50"),
        "carbohydrates": Decimal("25.00"),
        "fat": Decimal("0.30"),
        "fiber": Decimal("4.40"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Cooked Oatmeal",
        "description": "Rolled oats cooked in water",
        "category": "GRAIN",
        "serving_size": Decimal("100.00"),
        "serving_unit": "gram",
        "calories": Decimal("71.00"),
        "protein": Decimal("2.50"),
        "carbohydrates": Decimal("12.00"),
        "fat": Decimal("1.40"),
        "fiber": Decimal("1.70"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Filter Coffee with Milk",
        "description": "South Indian filter coffee prepared with whole milk and 1 tsp sugar (approx. 150ml)",
        "category": "BEVERAGE",
        "serving_size": Decimal("1.00"),
        "serving_unit": "cup",
        "calories": Decimal("75.00"),
        "protein": Decimal("2.50"),
        "carbohydrates": Decimal("9.50"),
        "fat": Decimal("3.00"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Black Coffee",
        "description": "Brewed black coffee without milk or sugar",
        "category": "BEVERAGE",
        "serving_size": Decimal("200.00"),
        "serving_unit": "ml",
        "calories": Decimal("2.00"),
        "protein": Decimal("0.30"),
        "carbohydrates": Decimal("0.00"),
        "fat": Decimal("0.00"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Masala Chai",
        "description": "Indian spiced milk tea brewed with milk and 1 tsp sugar (approx. 150ml)",
        "category": "BEVERAGE",
        "serving_size": Decimal("1.00"),
        "serving_unit": "cup",
        "calories": Decimal("85.00"),
        "protein": Decimal("2.50"),
        "carbohydrates": Decimal("12.00"),
        "fat": Decimal("2.80"),
        "fiber": Decimal("0.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Almonds",
        "description": "Whole raw unsalted almond kernels (approx. 23 kernels)",
        "category": "SNACK",
        "serving_size": Decimal("30.00"),
        "serving_unit": "gram",
        "calories": Decimal("173.00"),
        "protein": Decimal("6.00"),
        "carbohydrates": Decimal("6.10"),
        "fat": Decimal("15.00"),
        "fiber": Decimal("3.50"),
        "source": "INTERNAL_DEV_DATASET",
    },
    {
        "name": "Peanut Butter",
        "description": "Smooth natural roasted peanut butter",
        "category": "LEGUME",
        "serving_size": Decimal("16.00"),
        "serving_unit": "gram",
        "calories": Decimal("95.00"),
        "protein": Decimal("4.00"),
        "carbohydrates": Decimal("3.50"),
        "fat": Decimal("8.00"),
        "fiber": Decimal("1.00"),
        "source": "INTERNAL_DEV_DATASET",
    },
]


def seed_foods(db: Session) -> int:
    """
    Idempotently seeds all baseline foods into the database.
    Returns the count of seeded/verified items.
    """
    count = 0
    for food_dict in INITIAL_FOODS:
        food_in = FoodItemCreate(**food_dict)
        food_service.upsert_food(db, food_in)
        count += 1
    logger.info(f"Seeded/updated {count} baseline food items successfully.")
    return count


if __name__ == "__main__":
    db = SessionLocal()
    try:
        total = seed_foods(db)
        print(f"Successfully seeded {total} baseline food items.")
    finally:
        db.close()
