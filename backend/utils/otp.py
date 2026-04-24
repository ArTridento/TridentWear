import random
import string
from datetime import datetime, timedelta
from config import get_settings
import logging
from utils.hashing import hash_password, verify_password

logger = logging.getLogger(__name__)

settings = get_settings()


def generate_otp(length: int = None) -> str:
    """
    Generate a random numeric OTP.

    Args:
        length: Length of OTP (default from settings)

    Returns:
        OTP string of digits
    """
    if length is None:
        length = settings.OTP_LENGTH

    otp = "".join(random.choices(string.digits, k=length))
    logger.info(f"Generated OTP (for logging only, not actual value)")
    return otp


def hash_otp(otp: str) -> str:
    """
    Hash OTP for secure storage in database.

    Args:
        otp: Plaintext OTP

    Returns:
        Hashed OTP
    """
    return hash_password(otp)


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """
    Verify plaintext OTP against hashed OTP.

    Args:
        plain_otp: OTP from user
        hashed_otp: Hashed OTP from database

    Returns:
        True if OTP matches
    """
    return verify_password(plain_otp, hashed_otp)


def is_otp_expired(otp_expiry: datetime) -> bool:
    """
    Check if OTP has expired.

    Args:
        otp_expiry: Expiry datetime from database

    Returns:
        True if expired, False if still valid
    """
    if otp_expiry is None:
        return True

    return datetime.utcnow() > otp_expiry


def get_otp_expiry() -> datetime:
    """
    Get OTP expiry datetime (current time + OTP_EXPIRY_MINUTES).

    Returns:
        Datetime object for OTP expiry
    """
    return datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
