from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from config import get_settings
from database import create_all_tables
from routers import auth_router, products_router, orders_router, payments_router
from middleware.security import add_security_headers, setup_cors, setup_trusted_hosts
from middleware.rate_limit import limiter, rate_limit_exception_handler
from slowapi.errors import RateLimitExceeded
import logging
from logging.config import dictConfig

settings = get_settings()

# ========== LOGGING CONFIGURATION ==========
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "formatter": "detailed",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/tridentwear.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# ========== LIFESPAN EVENTS ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """
    # ========== ON STARTUP ==========
    logger.info("🚀 Starting TridentWear API...")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Unknown'}")

    try:
        create_all_tables()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise

    yield

    # ========== ON SHUTDOWN ==========
    logger.info("🛑 Shutting down TridentWear API...")


# ========== CREATE FASTAPI APP ==========
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade eCommerce API",
    version=settings.APP_VERSION,
    openapi_url="/api/docs" if not settings.DEBUG else "/api/openapi.json",
    lifespan=lifespan,
)

# ========== ADD STATE LIMITER ==========
app.state.limiter = limiter

# ========== MIDDLEWARE SETUP ==========
# Order matters: these run in reverse order

# 1. Security headers (runs last, so headers are added to every response)
app.middleware("http")(add_security_headers)

# 2. CORS must be added before trusted hosts
setup_cors(app, settings)

# 3. Trusted hosts
setup_trusted_hosts(app, settings)

# ========== EXCEPTION HANDLERS ==========


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return await rate_limit_exception_handler(request, exc)


# ========== INCLUDE ROUTERS ==========
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)


# ========== HEALTH CHECK ENDPOINT ==========
@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": "debug" if settings.DEBUG else "production",
    }


# ========== ROOT ENDPOINT ==========
@app.get("/")
async def root():
    """
    API root endpoint with documentation links.
    """
    return {
        "message": "Welcome to TridentWear API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/health",
    }


# ========== ERROR HANDLER FOR 404 ==========
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested resource was not found",
            "path": str(request.url),
        },
    )


# ========== ERROR HANDLER FOR 500 ==========
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
        },
    )


# ========== STARTUP LOGGING ==========
@app.on_event("startup")
async def startup_logging():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info(f"API: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Rate Limiting: {settings.RATE_LIMIT_ENABLED}")
    logger.info(f"CORS Origins: {', '.join(settings.CORS_ORIGINS)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
