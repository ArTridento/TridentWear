import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class User(Base):
    """
    User model for authentication and customer data.
    Stores hashed passwords, never plaintext.
    """

    __tablename__ = "users"

    # ========== PRIMARY KEY ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========== AUTH FIELDS ==========
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Bcrypt hash, never plaintext

    # ========== USER PROFILE ==========
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True, default="India")

    # ========== ACCOUNT STATUS ==========
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # ========== OTP FIELDS ==========
    otp = Column(String(6), nullable=True)  # Stored hashed
    otp_expiry = Column(DateTime, nullable=True)

    # ========== TIMESTAMPS ==========
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
