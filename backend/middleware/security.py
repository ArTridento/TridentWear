from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

logger = logging.getLogger(__name__)


async def add_security_headers(request: Request, call_next):
    """
    Middleware to add security headers to all responses.
    """
    response = await call_next(request)

    # ========== SECURITY HEADERS ==========
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Enable XSS protection (legacy, but still useful)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Strict Transport Security (force HTTPS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Content Security Policy (strict)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"

    # Disable referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Prevent search engines from indexing
    response.headers["X-Robots-Tag"] = "noindex, nofollow"

    return response


def setup_cors(app, settings):
    """
    Configure CORS for the application.

    Args:
        app: FastAPI application
        settings: Settings object with CORS_ORIGINS
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # Specific origins only (NOT "*")
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        expose_headers=["X-Total-Count", "X-Page"],
        max_age=600,  # Cache preflight for 10 minutes
    )


def setup_trusted_hosts(app, settings):
    """
    Configure trusted hosts middleware.

    Args:
        app: FastAPI application
        settings: Settings object
    """
    # Only in production - add your domain
    allowed_hosts = [
        "localhost",
        "localhost:8000",
        "127.0.0.1",
        "tridentwear.com",
        "www.tridentwear.com",
        "api.tridentwear.com",
    ]

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )
