"""
Food service handling food item lookup, search, and catalog management.
Decouples query and business logic from API endpoints.
"""

from typing import List, Optional
from sqlalchemy import select, case
from sqlalchemy.orm import Session
from app.models.food import FoodItem
from app.schemas.food import FoodItemCreate


class FoodService:
    @staticmethod
    def get_by_id(db: Session, food_id: int) -> Optional[FoodItem]:
        """Retrieve a food item by primary key ID."""
        stmt = select(FoodItem).where(FoodItem.id == food_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[FoodItem]:
        """Retrieve a food item by exact case-insensitive name."""
        stmt = select(FoodItem).where(FoodItem.name.ilike(name.strip()))
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def search(
        db: Session,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[FoodItem]:
        """
        Perform case-insensitive search on food names and descriptions.
        Ranks results with exact matches first, followed by prefix matches, then substring matches.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # Bound pagination limit
        safe_limit = max(1, min(limit, 50))
        safe_offset = max(0, offset)

        search_filter = FoodItem.name.ilike(f"%{clean_query}%") | FoodItem.description.ilike(f"%{clean_query}%")
        stmt = select(FoodItem).where(search_filter)

        if category:
            stmt = stmt.where(FoodItem.category == category.strip().upper())

        # Relevance ranking: exact name match > prefix match > substring
        relevance_order = case(
            (FoodItem.name.ilike(clean_query), 1),
            (FoodItem.name.ilike(f"{clean_query}%"), 2),
            else_=3,
        )

        stmt = stmt.order_by(relevance_order, FoodItem.name.asc()).limit(safe_limit).offset(safe_offset)
        return list(db.execute(stmt).scalars().all())

    @classmethod
    def upsert_food(cls, db: Session, food_in: FoodItemCreate) -> FoodItem:
        """
        Idempotently create or update a food item by name.
        Safe for initial catalog seeding and migrations.
        """
        existing = cls.get_by_name(db, food_in.name)
        data = food_in.model_dump()

        if existing is None:
            food_item = FoodItem(**data)
            db.add(food_item)
        else:
            for field, value in data.items():
                setattr(existing, field, value)
            food_item = existing

        db.commit()
        db.refresh(food_item)
        return food_item


food_service = FoodService()
