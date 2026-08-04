import pytest
from pydantic import ValidationError

from app.models.calculation import CalculationFactory
from app.schemas.calculation import CalculationCreate, CalculationType


@pytest.mark.parametrize(
    "a, b, calc_type, expected",
    [
        (2, 3, "Add", 5.0),
        (5, 2, "Sub", 3.0),
        (4, 6, "Multiply", 24.0),
        (10, 2, "Divide", 5.0),
    ],
    ids=[
        "add",
        "subtract",
        "multiply",
        "divide",
    ]
)
def test_valid_calculation_create(a, b, calc_type, expected):
    calc = CalculationCreate(
        a=a,
        b=b,
        type=calc_type,
    )

    assert calc.a == float(a)
    assert calc.b == float(b)
    assert calc.type == CalculationType(calc_type.lower())
    assert CalculationFactory.compute(calc.a, calc.b, calc.type) == expected


def test_invalid_operation_type():
    with pytest.raises(ValidationError):
        CalculationCreate(
            a=5,
            b=2,
            type="Power",
        )


def test_divide_by_zero():
    with pytest.raises(ValueError):
        CalculationCreate(
            a=10,
            b=0,
            type="Divide",
        )