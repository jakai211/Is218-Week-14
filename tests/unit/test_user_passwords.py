import pytest
from pydantic import ValidationError

from app.models.user import User, hash_password, verify_password
from app.schemas.user import UserRead


def test_hash_and_verify_password_round_trip():
    raw_password = "SecurePass123"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPass123", hashed) is False


def test_user_read_schema_excludes_password_hash():
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        username="janedoe",
        password="SecurePass123",
    )

    read_model = UserRead.model_validate(user)

    assert read_model.username == "janedoe"
    assert read_model.email == "jane@example.com"
    assert not hasattr(read_model, "password_hash")


def test_user_create_schema_rejects_invalid_email():
    with pytest.raises(ValidationError):
        from app.schemas.base import UserCreate

        UserCreate(
            username="janedoe",
            email="not-an-email",
            password="SecurePass123",
        )
