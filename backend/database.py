from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

# ========== ENGINE CONFIGURATION ==========
# Using connection pooling for production
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=pool.NullPool,  # Use NullPool to avoid connection issues in production
    echo=settings.DEBUG,
    connect_args={
        "connect_timeout": 10,
        "application_name": "tridentwear_api",
    },
)

# ========== SESSION FACTORY ==========
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ========== BASE FOR MODELS ==========
Base = declarative_base()


# ========== DEPENDENCY INJECTION ==========
def get_db() -> Session:
    """
    FastAPI dependency to get database session.
    Ensures session is properly closed after request.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()


# ========== CREATE ALL TABLES ==========
def create_all_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


# ========== DROP ALL TABLES (ONLY FOR DEVELOPMENT) ==========
def drop_all_tables():
    """Drop all tables - ONLY USE IN DEVELOPMENT"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")