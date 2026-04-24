from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from config import get_settings
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

settings = get_settings()


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        subject: User ID or email to encode in token
        expires_delta: Optional custom expiry time

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: User ID or email to encode in token

    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        token_type: Type of token ("access" or "refresh")

    Returns:
        Subject (user ID) if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None

        subject: str = payload.get("sub")

        if subject is None:
            logger.warning("Token has no subject")
            return None

        return subject

    except JWTError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        return None


def get_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract and parse user ID from token.

    Args:
        token: JWT token

    Returns:
        UUID of user if valid, None otherwise
    """
    user_id_str = verify_token(token, token_type="access")

    if not user_id_str:
        return None

    try:
        return UUID(user_id_str)
    except ValueError:
        logger.error(f"Invalid UUID in token: {user_id_str}")
        return None
