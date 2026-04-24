from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# ========== PASSWORD HASHING CONTEXT ==========
# Using bcrypt for password hashing (industry standard, slow by design)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Higher rounds = slower = more secure
)


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password: Plaintext password to hash

    Returns:
        Hashed password safe for database storage
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: Plaintext password from user
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a hash needs to be rehashed (e.g., if rounds changed).

    Args:
        hashed_password: Hashed password to check

    Returns:
        True if rehashing is recommended
    """
    return pwd_context.needs_update(hashed_password)
