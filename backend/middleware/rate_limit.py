from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# ========== RATE LIMITER INSTANCE ==========
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom error handler for rate limit exceeded.

    Returns:
        JSON response with proper status code
    """
    logger.warning(f"Rate limit exceeded for IP: {get_remote_address(request)}")

    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "detail": "Rate limit exceeded. Try again later.",
            "retry_after": exc.detail.split("called ")[-1].split(" times")[0] if exc.detail else "60 seconds",
        },
    )


# ========== RATE LIMIT CONFIGURATIONS ==========
RATE_LIMIT_STRICT = "5/minute"  # Strict: auth endpoints (login, register)
RATE_LIMIT_NORMAL = "30/minute"  # Normal: general endpoints
RATE_LIMIT_GENEROUS = "100/minute"  # Generous: product list, reading
