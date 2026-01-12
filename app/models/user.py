"""User model."""

from passlib.hash import bcrypt
from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Hash and set password."""
        import re

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character")

        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        """Check if password matches hash."""
        return bcrypt.verify(password, self.password_hash)

    def to_dict(self):
        """Convert user to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "email": self.email,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "is_active": self.is_active,
                "last_login": self.last_login.isoformat() if self.last_login else None,
            }
        )
        return data

    def __repr__(self):
        return f"<User {self.email}>"
