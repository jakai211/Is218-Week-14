from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalculationType(str, Enum):
    add = "add"
    subtract = "subtract"
    multiply = "multiply"
    divide = "divide"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"add", "addition", "plus"}:
                return cls.add
            if normalized in {"subtract", "sub", "minus"}:
                return cls.subtract
            if normalized in {"multiply", "mul", "times"}:
                return cls.multiply
            if normalized in {"divide", "div", "division"}:
                return cls.divide
        return super()._missing_(value)


class CalculationCreate(BaseModel):
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    type: CalculationType = Field(..., description="Calculation type")

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_division(cls, values):
        if values.type == CalculationType.divide and values.b == 0:
            raise ValueError("Division by zero is not allowed")
        return values


class CalculationRead(BaseModel):
    id: str
    a: float
    b: float
    type: CalculationType
    result: float

    model_config = ConfigDict(from_attributes=True)
