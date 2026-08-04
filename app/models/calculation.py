from typing import Any, Dict

from sqlalchemy import Column, Float, String

from app.database import Base
from app.schemas.calculation import CalculationCreate


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)
    result = Column(Float, nullable=False)

    def __init__(self, **kwargs):
        calc_type = kwargs.get("type")
        if calc_type is not None:
            kwargs["type"] = calc_type.lower()
        if "result" not in kwargs:
            kwargs["result"] = self._compute_result(kwargs.get("a"), kwargs.get("b"), kwargs.get("type"))
        super().__init__(**kwargs)

    def _compute_result(self, a, b, calc_type):
        if calc_type == "add":
            return a + b
        if calc_type == "subtract":
            return a - b
        if calc_type == "multiply":
            return a * b
        if calc_type == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        raise ValueError("Invalid calculation type")

    @classmethod
    def create(cls, db, data: Dict[str, Any]) -> "Calculation":
        schema = CalculationCreate.model_validate(data)
        calculation = cls(a=schema.a, b=schema.b, type=schema.type)
        db.add(calculation)
        db.flush()
        return calculation
