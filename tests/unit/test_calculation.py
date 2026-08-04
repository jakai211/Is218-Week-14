import pytest
from pydantic import ValidationError

from app.schemas.calculation import CalculationCreate


@pytest.mark.parametrize(
    "a, b, calc_type",
    [
        (2, 3, "Add"),
        (5, 2, "Sub"),
        (4, 6, "Multiply"),
        (10, 2, "Divide"),
    ],
    ids=[
        "add",
        "subtract",
        "multiply",
        "divide",
    ]
)
def test_valid_calculation_create(a, b, calc_type):
    calc = CalculationCreate(
        a=a,
        b=b,
        type=calc_type,
    )

    assert calc.a == a
    assert calc.b == b
    assert calc.type == calc_type


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