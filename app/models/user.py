# app/models/user.py
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base

from app.schemas.base import UserCreate
from app.schemas.user import Token, UserResponse

Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(50), nullable=False, default="")
    last_name = Column(String(50), nullable=False, default="")
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        password = kwargs.pop("password", None)
        password_hash = kwargs.pop("password_hash", None)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_verified", False)
        if password is not None:
            if password.startswith("$2") and len(password) > 20:
                kwargs["password_hash"] = password
            else:
                kwargs["password_hash"] = hash_password(password)
        elif password_hash is not None:
            kwargs["password_hash"] = password_hash
        super().__init__(**kwargs)

    @property
    def password(self) -> str:
        return self.password_hash

    @password.setter
    def password(self, value: str) -> None:
        self.password_hash = hash_password(value) if value else value

    def __repr__(self):
        return f"<User(name={self.first_name} {self.last_name}, email={self.email})>"

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return hash_password(password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify a plain password against the stored hash."""
        return verify_password(plain_password, self.password_hash)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[uuid.UUID]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            return str(user_id) if user_id else None
        except (JWTError, ValueError):
            return None

    @classmethod
    def register(cls, db, user_data: Dict[str, Any]) -> "User":
        """Register a new user with validation."""
        try:
            password = user_data.get("password", "")
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")

            user_create = UserCreate.model_validate(user_data)
            new_user = cls(
                first_name=user_create.first_name or "",
                last_name=user_create.last_name or "",
                email=user_create.email,
                username=user_create.username,
                password=user_create.password,
                is_active=True,
                is_verified=False,
            )

            db.add(new_user)
            db.flush()
            return new_user
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Username or email already exists") from exc
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
        except ValueError:
            raise

    @classmethod
    def authenticate(cls, db, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return token with user data."""
        user = db.query(cls).filter(
            (cls.username == username) | (cls.email == username)
        ).first()

        if not user or not user.verify_password(password):
            return None

        user.last_login = datetime.utcnow()
        db.commit()

        user_response = UserResponse.model_validate(user)
        token_response = Token(
            access_token=cls.create_access_token({"sub": str(user.id)}),
            token_type="bearer",
            user=user_response,
        )

        return token_response.model_dump()