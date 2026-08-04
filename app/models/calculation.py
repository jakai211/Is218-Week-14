from typing import Any, Dict

from sqlalchemy import Column, Float, String

from app.database import Base
from app.schemas.calculation import CalculationCreate, CalculationType


class CalculationFactory:
    """Factory responsible for constructing calculation results."""

    @classmethod
    def compute(cls, a: float, b: float, calc_type: CalculationType) -> float:
        if calc_type == CalculationType.add:
            return a + b
        if calc_type == CalculationType.subtract:
            return a - b
        if calc_type == CalculationType.multiply:
            return a * b
        if calc_type == CalculationType.divide:
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        raise ValueError("Invalid calculation type")


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)
    result = Column(Float, nullable=False)

    def __init__(self, **kwargs):
        calc_type = kwargs.get("type")
        if isinstance(calc_type, CalculationType):
            kwargs["type"] = calc_type.value
        elif calc_type is not None:
            kwargs["type"] = str(calc_type).lower()

        if "result" not in kwargs:
            kwargs["result"] = self._compute_result(kwargs.get("a"), kwargs.get("b"), kwargs.get("type"))
        super().__init__(**kwargs)

    @classmethod
    def _compute_result(cls, a, b, calc_type):
        if a is None or b is None or calc_type is None:
            raise ValueError("Calculation requires a, b, and type")
        return CalculationFactory.compute(a, b, CalculationType(calc_type))

    @classmethod
    def create(cls, db, data: Dict[str, Any]) -> "Calculation":
        schema = CalculationCreate.model_validate(data)
        result = CalculationFactory.compute(schema.a, schema.b, schema.type)
        calculation = cls(a=schema.a, b=schema.b, type=schema.type.value, result=result)
        db.add(calculation)
        db.flush()
        return calculation
