from sqlalchemy.orm import Session
from sqlalchemy import select
from models.user import User
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_refresh_token
from utils.otp import generate_otp, hash_otp, verify_otp, is_otp_expired, get_otp_expiry
from schemas.user import UserRegister, TokenResponse
from typing import Optional, Dict, Any
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication business logic"""

    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: Registration data

        Returns:
            User data and tokens
        """
        # ========== CHECK IF USER EXISTS ==========
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("User with this email already exists")

        # ========== CREATE NEW USER ==========
        user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"New user registered: {user.email}")

        # ========== GENERATE TOKENS ==========
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
            "access_token": create_access_token(str(user.id)),
            "refresh_token": create_refresh_token(str(user.id)),
        }

    @staticmethod
    def login_user(db: Session, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return tokens.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            User data and tokens
        """
        # ========== FIND USER ==========
        user = db.query(User).filter(User.email == email).first()

        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise ValueError("Invalid email or password")

        # ========== VERIFY PASSWORD ==========
        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {email}")
            raise ValueError("Invalid email or password")

        # ========== CHECK IF ACCOUNT IS ACTIVE ==========
        if not user.is_active:
            logger.warning(f"Login attempt on inactive account: {email}")
            raise ValueError("Account is inactive")

        # ========== UPDATE LAST LOGIN ==========
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.commit()

        logger.info(f"User logged in: {email}")

        # ========== GENERATE TOKENS ==========
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
            "access_token": create_access_token(str(user.id)),
            "refresh_token": create_refresh_token(str(user.id)),
        }

    @staticmethod
    def send_otp(db: Session, email: str) -> Dict[str, str]:
        """
        Generate and send OTP to user email.

        Args:
            db: Database session
            email: User email

        Returns:
            Confirmation message
        """
        # ========== FIND OR CREATE USER ==========
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create unverified user for OTP
            user = User(
                email=email,
                password_hash="",  # Placeholder, will be set on registration
                full_name="",
            )
            db.add(user)

        # ========== GENERATE OTP ==========
        otp = generate_otp()
        user.otp = hash_otp(otp)
        user.otp_expiry = get_otp_expiry()
        db.commit()

        logger.info(f"OTP generated for email: {email}")

        # ========== IN PRODUCTION, SEND EMAIL HERE ==========
        # This is where you'd call email_service.send_otp_email(email, otp)
        # For now, return success (email will be sent by email service)

        return {
            "message": "OTP sent to email",
            "email": email,
        }

    @staticmethod
    def verify_otp(db: Session, email: str, otp: str) -> Dict[str, Any]:
        """
        Verify OTP and mark user as verified.

        Args:
            db: Database session
            email: User email
            otp: OTP from user

        Returns:
            User data and tokens
        """
        # ========== FIND USER ==========
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise ValueError("User not found")

        # ========== CHECK IF OTP EXISTS ==========
        if not user.otp:
            raise ValueError("No OTP found for this user")

        # ========== CHECK IF OTP EXPIRED ==========
        if is_otp_expired(user.otp_expiry):
            raise ValueError("OTP has expired")

        # ========== VERIFY OTP ==========
        if not verify_otp(otp, user.otp):
            logger.warning(f"Failed OTP verification for: {email}")
            raise ValueError("Invalid OTP")

        # ========== MARK AS VERIFIED ==========
        user.is_verified = True
        user.otp = None
        user.otp_expiry = None
        db.commit()

        logger.info(f"OTP verified for: {email}")

        # ========== GENERATE TOKENS ==========
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
            "access_token": create_access_token(str(user.id)),
            "refresh_token": create_refresh_token(str(user.id)),
        }

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            User object or None
        """
        return db.query(User).filter(User.id == user_id).first()
