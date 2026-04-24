from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Production-grade settings with environment variable support"""

    # ========== DATABASE ==========
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/tridentwear"

    # ========== JWT CONFIGURATION ==========
    SECRET_KEY: str  # Must be set in .env - use: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ========== OTP CONFIGURATION ==========
    OTP_EXPIRY_MINUTES: int = 10
    OTP_LENGTH: int = 6

    # ========== RAZORPAY CONFIGURATION ==========
    RAZORPAY_KEY_ID: str  # Must be set in .env
    RAZORPAY_KEY_SECRET: str  # Must be set in .env
    RAZORPAY_WEBHOOK_SECRET: str  # Must be set in .env

    # ========== EMAIL CONFIGURATION ==========
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str  # Must be set in .env
    SMTP_PASSWORD: str  # Must be set in .env (use app-specific password)
    SENDER_EMAIL: str = "noreply@tridentwear.com"

    # ========== SECURITY CONFIGURATION ==========
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://tridentwear.com",
    ]

    # ========== RATE LIMITING ==========
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_PERIOD_SECONDS: int = 60

    # ========== APP CONFIGURATION ==========
    APP_NAME: str = "TridentWear API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
