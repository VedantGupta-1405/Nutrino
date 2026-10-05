"""
Unit tests for deterministic nutrition calculator.
Validates precision, unit scaling, dimensional compatibility, and boundary constraints.
"""

from decimal import Decimal
import pytest
from app.models.food import FoodItem
from app.nutrition.calculator import nutrition_calculator, compute_scaling_factor
from app.exceptions.base import ValidationException


@pytest.fixture
def mock_rice():
    """Mock 100g serving of cooked white rice."""
    return FoodItem(
        id=1,
        name="Cooked White Rice",
        serving_size=Decimal("100.00"),
        serving_unit="gram",
        calories=Decimal("130.00"),
        protein=Decimal("2.70"),
        carbohydrates=Decimal("28.20"),
        fat=Decimal("0.30"),
        fiber=Decimal("0.40"),
    )


@pytest.fixture
def mock_dosa():
    """Mock 1 piece serving of plain dosa."""
    return FoodItem(
        id=2,
        name="Plain Dosa",
        serving_size=Decimal("1.00"),
        serving_unit="piece",
        calories=Decimal("133.00"),
        protein=Decimal("2.70"),
        carbohydrates=Decimal("18.80"),
        fat=Decimal("5.20"),
        fiber=Decimal("1.10"),
    )


@pytest.fixture
def mock_milk():
    """Mock 250ml serving of whole milk."""
    return FoodItem(
        id=3,
        name="Whole Milk",
        serving_size=Decimal("250.00"),
        serving_unit="ml",
        calories=Decimal("152.00"),
        protein=Decimal("8.00"),
        carbohydrates=Decimal("12.00"),
        fat=Decimal("8.00"),
        fiber=Decimal("0.00"),
    )


def test_gram_based_scaling(mock_rice):
    """Test scaling 100g rice to 200g produces exact 2x nutrients."""
    res = nutrition_calculator.calculate(mock_rice, quantity=200, unit="gram")
    assert res.food_name == "Cooked White Rice"
    assert res.quantity == Decimal("200")
    assert res.calories == Decimal("260.00")
    assert res.protein == Decimal("5.40")
    assert res.carbohydrates == Decimal("56.40")
    assert res.fat == Decimal("0.60")
    assert res.fiber == Decimal("0.80")


def test_weight_unit_conversion_kg_to_gram(mock_rice):
    """Test converting 0.5 kg to 100g base serving (5x factor)."""
    res = nutrition_calculator.calculate(mock_rice, quantity=0.5, unit="kg")
    assert res.calories == Decimal("650.00")
    assert res.protein == Decimal("13.50")
    assert res.carbohydrates == Decimal("141.00")
    assert res.fat == Decimal("1.50")
    assert res.fiber == Decimal("2.00")


def test_piece_based_scaling(mock_dosa):
    """Test scaling 1 piece dosa to 2 pieces."""
    res = nutrition_calculator.calculate(mock_dosa, quantity=2, unit="piece")
    assert res.calories == Decimal("266.00")
    assert res.protein == Decimal("5.40")
    assert res.carbohydrates == Decimal("37.60")
    assert res.fat == Decimal("10.40")
    assert res.fiber == Decimal("2.20")


def test_piece_alias_unit(mock_dosa):
    """Test unit aliases like 'pieces', 'pc', 'pcs' match 'piece'."""
    res = nutrition_calculator.calculate(mock_dosa, quantity=3, unit="pieces")
    assert res.calories == Decimal("399.00")
    assert res.protein == Decimal("8.10")


def test_decimal_quantities(mock_dosa):
    """Test fractional servings (e.g. 1.5 dosas)."""
    res = nutrition_calculator.calculate(mock_dosa, quantity="1.5", unit="piece")
    # 133 * 1.5 = 199.50
    assert res.calories == Decimal("199.50")
    # 2.7 * 1.5 = 4.05
    assert res.protein == Decimal("4.05")
    # 18.8 * 1.5 = 28.20
    assert res.carbohydrates == Decimal("28.20")
    # 5.2 * 1.5 = 7.80
    assert res.fat == Decimal("7.80")


def test_volume_unit_conversion_liter_to_ml(mock_milk):
    """Test converting 1 liter to 250ml base serving (4x factor)."""
    res = nutrition_calculator.calculate(mock_milk, quantity=1, unit="liter")
    assert res.calories == Decimal("608.00")
    assert res.protein == Decimal("32.00")
    assert res.carbohydrates == Decimal("48.00")
    assert res.fat == Decimal("32.00")


def test_incompatible_unit_conversion_rejected(mock_dosa, mock_rice):
    """Test requesting weight for piece-based food raises ValidationException."""
    with pytest.raises(ValidationException) as exc_info:
        nutrition_calculator.calculate(mock_dosa, quantity=100, unit="gram")
    assert "Cannot convert" in str(exc_info.value)
    assert "piece" in str(exc_info.value)

    # Requesting pieces for gram-based food
    with pytest.raises(ValidationException):
        nutrition_calculator.calculate(mock_rice, quantity=2, unit="piece")


def test_invalid_negative_or_zero_quantity(mock_rice):
    """Test negative or zero quantity raises ValidationException."""
    with pytest.raises(ValidationException) as exc1:
        nutrition_calculator.calculate(mock_rice, quantity=0, unit="gram")
    assert "greater than zero" in str(exc1.value)

    with pytest.raises(ValidationException) as exc2:
        nutrition_calculator.calculate(mock_rice, quantity=-50, unit="gram")
    assert "greater than zero" in str(exc2.value)
