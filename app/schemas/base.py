from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, model_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""

    first_name: str = Field(default="", max_length=50, example="John")
    last_name: str = Field(default="", max_length=50, example="Doe")
    email: EmailStr = Field(example="john.doe@example.com")
    username: str = Field(min_length=3, max_length=50, example="johndoe")

    model_config = ConfigDict(from_attributes=True)


class PasswordMixin(BaseModel):
    """Mixin for password validation."""

    password: str = Field(min_length=6, max_length=128, example="SecurePass123")

    @model_validator(mode="before")
    @classmethod
    def validate_password(cls, values):
        if isinstance(values, dict):
            password = values.get("password")
            if not password:
                raise ValueError("Password is required")
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            if not any(char.isupper() for char in password):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(char.islower() for char in password):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(char.isdigit() for char in password):
                raise ValueError("Password must contain at least one digit")
        return values


class UserCreate(UserBase, PasswordMixin):
    """Schema for creating a new user."""

    pass


class UserLogin(PasswordMixin):
    """Schema for user login."""

    username: str = Field(
        description="Username or email",
        min_length=3,
        max_length=50,
        example="johndoe123",
    )
